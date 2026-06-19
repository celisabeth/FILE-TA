#!/usr/bin/env python3
"""
Pengukuran eksperimen AQE — BAB IV §4.1.3–§4.1.6 (fokus Silver).

Subperintah:
  partition-skew   — distribusi partisi & skew key (prodi_id) pada tabel Silver
  components     — durasi workload W1–W3 per profil komponen AQE
  format         — perbandingan Parquet / ORC / JSON (write+read)
  silver-summary — ringkasan metrik layer Silver (pipeline + workload + skew)
  all            — jalankan semua di atas

Output: metrics/aqe_measurement_{jenis}_{timestamp}.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark._common import metrics_dir, utc_now, write_json
from benchmark.workloads import spark_silver_workloads
from spark.aqe_component_config import COMPONENT_PROFILES, profile_component_labels, spark_configs_for_profile
from spark.aqe_config import read_applied_aqe_configs, resolve_aqe_scenario
from spark.bronze_to_silver_aqe import get_spark_session
from spark.lakehouse_catalog import SHARED_CATALOG, silver_schema, silver_table

logger = logging.getLogger("benchmark.measure_aqe")


def _spark_for_profile(profile: str, aqe_scenario: str = "ON"):
    """Session Spark dengan profil komponen (basis skenario OFF/ON untuk warehouse)."""
    from pyspark.sql import SparkSession

    from spark.bronze_to_silver_aqe import _resolve_jars
    from spark.lakehouse_catalog import apply_hadoop_s3a, configure_spark_catalog
    from spark.spark_python import apply_cluster_resource_configs, apply_pyspark_python_configs
    from spark.aqe_config import app_name_with_aqe

    scenario = resolve_aqe_scenario(aqe_scenario)
    configs = spark_configs_for_profile(profile, scenario)

    import socket

    spark_master = os.environ.get("SPARK_MASTER", "spark://spark-master:7077")
    try:
        sock = socket.create_connection(("spark-master", 7077), timeout=5)
        sock.close()
    except (OSError, socket.timeout):
        spark_master = "local[*]"

    builder = configure_spark_catalog(
        SparkSession.builder.appName(
            app_name_with_aqe(f"aqe_measure_{profile}", scenario)
        ).master(spark_master),
        scenario,
    )
    jars = _resolve_jars()
    if jars:
        builder = builder.config("spark.jars", jars)
    builder = apply_pyspark_python_configs(builder)
    builder = apply_cluster_resource_configs(builder)
    for k, v in configs.items():
        builder = builder.config(k, v)
    spark = builder.getOrCreate()
    return spark, configs


def _skew_stats(counts: list[int]) -> dict[str, float]:
    if not counts:
        return {"row_count_total": 0, "key_count": 0}
    total = sum(counts)
    n = len(counts)
    mean = total / n
    mx = max(counts)
    mn = min(counts)
    sorted_c = sorted(counts)
    p95_idx = min(n - 1, int(n * 0.95))
    return {
        "row_count_total": total,
        "key_count": n,
        "min_rows_per_key": mn,
        "max_rows_per_key": mx,
        "mean_rows_per_key": round(mean, 2),
        "skew_ratio_max_over_mean": round(mx / mean, 3) if mean else None,
        "p95_rows_per_key": sorted_c[p95_idx],
        "top_key_share_pct": round(100.0 * mx / total, 2) if total else None,
    }


def measure_partition_skew(aqe_scenario: str = "ON") -> dict[str, Any]:
    """§4.1.3 — distribusi partisi shuffle & skew kolom join (prodi_id)."""
    scenario = resolve_aqe_scenario(aqe_scenario)
    silver = silver_schema(scenario)
    started = utc_now()
    from pyspark.sql import functions as F

    spark = get_spark_session(scenario)
    tables_report: dict[str, Any] = {}

    try:
        for table, key_col in (
            ("silver_mahasiswa", "prodi_id"),
            ("silver_dosen", "prodi_id"),
            ("silver_lulusan", "prodi_id"),
        ):
            fqn = silver_table(scenario, table)
            try:
                df = spark.table(fqn)
            except Exception as exc:
                tables_report[table] = {"fqn": fqn, "error": str(exc), "status": "missing"}
                continue

            row_count = df.count()
            shuffle_partitions = int(
                spark.conf.get("spark.sql.shuffle.partitions", "200")
            )
            rdd_parts = df.rdd.getNumPartitions()

            if key_col in df.columns:
                dist = (
                    df.groupBy(key_col)
                    .count()
                    .orderBy(F.col("count").desc())
                )
                top_rows = dist.limit(10).collect()
                counts = [int(r["count"]) for r in dist.collect()]
                skew = _skew_stats(counts)
                top_keys = [
                    {key_col: str(r[key_col]), "count": int(r["count"])} for r in top_rows
                ]
            else:
                skew = {}
                top_keys = []

            tables_report[table] = {
                "fqn": fqn,
                "row_count": row_count,
                "spark_shuffle_partitions_setting": shuffle_partitions,
                "dataframe_partitions": rdd_parts,
                "skew_key": key_col,
                "skew": skew,
                "top_keys": top_keys,
            }
    finally:
        spark.stop()

    ended = utc_now()
    payload = {
        "measurement": "partition_skew",
        "bab_section": "4.1.3",
        "layer": "silver",
        "aqe_scenario": scenario,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "tables": tables_report,
        "notes": (
            "skew_ratio > 3 mengindikasikan ketimpangan kuat; "
            "bandingkan dengan profil generate_data --profile aqe (skew ke prodi SD)."
        ),
    }
    out = _write_measurement("partition_skew", payload)
    payload["metrics_file"] = str(out)
    return payload


def measure_components(
    aqe_scenario: str = "ON",
    profiles: list[str] | None = None,
    workload_ids: list[str] | None = None,
) -> dict[str, Any]:
    """§4.1.4 — efektivitas komponen: coalesce, skew join, DPP, local shuffle."""
    scenario = resolve_aqe_scenario(aqe_scenario)
    profiles = profiles or list(COMPONENT_PROFILES)
    workload_ids = workload_ids or ["W1", "W2", "W3"]
    started = utc_now()
    profile_results: dict[str, Any] = {}

    for profile in profiles:
        logger.info("Profil komponen: %s", profile)
        spark, _cfg = _spark_for_profile(profile, scenario)
        applied = read_applied_aqe_configs(spark)
        workloads_out: dict[str, Any] = {}
        try:
            for wl in spark_silver_workloads(scenario):
                if wl["id"] not in workload_ids:
                    continue
                sql = wl["sql"].strip()
                t0 = time.perf_counter()
                try:
                    n = spark.sql(sql).count()
                    dur = round(time.perf_counter() - t0, 3)
                    workloads_out[wl["id"]] = {
                        "duration_sec": dur,
                        "row_count": n,
                        "status": "ok",
                    }
                except Exception as exc:
                    workloads_out[wl["id"]] = {"status": "error", "error": str(exc)}
        finally:
            spark.stop()

        profile_results[profile] = {
            "component_flags": profile_component_labels(profile),
            "spark_configs_effective": applied,
            "workloads": workloads_out,
        }

    ended = utc_now()
    payload = {
        "measurement": "aqe_components",
        "bab_section": "4.1.4",
        "layer": "silver",
        "aqe_scenario_data": scenario,
        "profiles_tested": profiles,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "profile_results": profile_results,
        "interpretation_hint": {
            "ON_COALESCE_ONLY": "Pengurangan partisi shuffle kecil pasca-stage",
            "ON_SKEW_ONLY": "Mitigasi join/agregasi pada key timpang (W1/W2)",
            "ON_DPP_ONLY": "Pruning partisi Iceberg saat join/filter (W3)",
            "ON_LOCAL_SHUFFLE_ONLY": "Membaca shuffle lokal tanpa jaringan",
            "ON_FULL": "Kombinasi semua komponen",
        },
    }
    out = _write_measurement("aqe_components", payload)
    payload["metrics_file"] = str(out)
    return payload


def measure_format_comparison(
    aqe_scenario: str = "ON",
    sample_rows: int = 50_000,
) -> dict[str, Any]:
    """§4.1.5 — perbandingan format file (Parquet, ORC, JSON) pada sampel Silver."""
    scenario = resolve_aqe_scenario(aqe_scenario)
    silver = silver_schema(scenario)
    started = utc_now()
    spark = get_spark_session(scenario)
    base_dir = metrics_dir() / "format_benchmark" / f"silver_{scenario.lower()}_{started.strftime('%Y%m%d_%H%M%S')}"
    base_dir.mkdir(parents=True, exist_ok=True)

    formats_report: dict[str, Any] = {}
    row_n = 0
    try:
        src = spark.table(silver_table(scenario, "silver_mahasiswa"))
        total = src.count()
        fraction = min(1.0, sample_rows / total) if total else 1.0
        sample = src.sample(withReplacement=False, fraction=fraction, seed=42)
        if sample_rows and total > sample_rows:
            sample = sample.limit(sample_rows)

        cached = sample.cache()
        row_n = cached.count()

        for fmt, write_mode in (
            ("parquet", {"format": "parquet"}),
            ("orc", {"format": "orc"}),
            ("json", {"format": "json"}),
        ):
            path = str(base_dir / fmt)
            t_w0 = time.perf_counter()
            cached.write.mode("overwrite").format(write_mode["format"]).save(path)
            write_sec = round(time.perf_counter() - t_w0, 3)
            size_bytes = sum(
                f.stat().st_size for f in Path(path).rglob("*") if f.is_file()
            )
            t_r0 = time.perf_counter()
            read_n = spark.read.format(write_mode["format"]).load(path).count()
            read_sec = round(time.perf_counter() - t_r0, 3)
            formats_report[fmt] = {
                "path": path,
                "rows": row_n,
                "write_duration_sec": write_sec,
                "read_duration_sec": read_sec,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 3),
                "read_row_count": read_n,
            }
        cached.unpersist()
    finally:
        spark.stop()

    ended = utc_now()
    payload = {
        "measurement": "format_comparison",
        "bab_section": "4.1.5",
        "layer": "silver",
        "aqe_scenario": scenario,
        "source_table": silver_table(scenario, "silver_mahasiswa"),
        "sample_rows": row_n,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "formats": formats_report,
        "notes": "Perbandingan serialisasi kolom; produksi memakai Iceberg/Parquet di MinIO.",
    }
    out = _write_measurement("format_comparison", payload)
    payload["metrics_file"] = str(out)
    return payload


def measure_silver_summary(aqe_scenario: str = "ON") -> dict[str, Any]:
    """§4.1.6 — hasil evaluasi per layer (hanya Silver yang diimplementasi penuh)."""
    from benchmark._common import find_latest_metric_file

    scenario = resolve_aqe_scenario(aqe_scenario)
    root = metrics_dir()
    if not (root / "runs").is_dir():
        try:
            from benchmark.experiment_run import root_metrics_dir

            root = root_metrics_dir()
        except Exception:
            pass

    pipeline_off = find_latest_metric_file(root, "bronze_to_silver_aqe_OFF_*.json")
    pipeline_on = find_latest_metric_file(root, "bronze_to_silver_aqe_ON_*.json")
    wl_off = find_latest_metric_file(root, "workloads_spark_aqe_OFF_*.json")
    wl_on = find_latest_metric_file(root, "workloads_spark_aqe_ON_*.json")
    skew_path = find_latest_metric_file(root, "aqe_measurement_partition_skew_*.json")
    components_path = find_latest_metric_file(root, "aqe_measurement_aqe_components_*.json")
    format_path = find_latest_metric_file(root, "aqe_measurement_format_comparison_*.json")

    def _load(p: Path | None) -> dict | None:
        if p and p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
        return None

    silver_tables = [
        "silver_mahasiswa",
        "silver_dosen",
        "silver_lulusan",
        "silver_penelitian_pkm",
        "silver_kerjasama_aktif",
        "silver_akreditasi_aktif",
    ]

    payload = {
        "measurement": "silver_layer_summary",
        "bab_section": "4.1.6",
        "layer": "silver",
        "scope_note": (
            "Gold & Trino (W4–W6) ada di repo tetapi pengukuran §4.1.3–4.1.5 "
            "difokuskan ke Silver + Iceberg AQE; lihat docs/eksperimen/pengukuran-aqe-4.1.3-4.1.6.md"
        ),
        "generated_at": utc_now().isoformat(),
        "catalog": SHARED_CATALOG,
        "schemas": {
            "OFF": silver_schema("OFF"),
            "ON": silver_schema("ON"),
        },
        "silver_tables_expected": silver_tables,
        "artifacts": {
            "pipeline_off": str(pipeline_off) if pipeline_off else None,
            "pipeline_on": str(pipeline_on) if pipeline_on else None,
            "workloads_off": str(wl_off) if wl_off else None,
            "workloads_on": str(wl_on) if wl_on else None,
            "partition_skew": str(skew_path) if skew_path else None,
            "aqe_components": str(components_path) if components_path else None,
            "format_comparison": str(format_path) if format_path else None,
        },
        "pipeline_duration_sec": {
            "OFF": (_load(pipeline_off) or {}).get("duration_sec"),
            "ON": (_load(pipeline_on) or {}).get("duration_sec"),
        },
        "workload_duration_sec": {
            "OFF": (_load(wl_off) or {}).get("workloads"),
            "ON": (_load(wl_on) or {}).get("workloads"),
        },
        "partition_skew_snapshot": (_load(skew_path) or {}).get("tables"),
    }
    out = _write_measurement("silver_layer_summary", payload)
    payload["metrics_file"] = str(out)
    return payload


def _write_measurement(kind: str, payload: dict[str, Any]) -> Path:
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    path = metrics_dir() / f"aqe_measurement_{kind}_{ts}.json"
    write_json(path, payload)
    logger.info("Wrote %s", path)
    return path


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="Pengukuran AQE §4.1.3–4.1.6 (Silver)")
    parser.add_argument(
        "command",
        choices=["partition-skew", "components", "format", "silver-summary", "all"],
    )
    parser.add_argument("--aqe-scenario", default="ON", choices=["OFF", "ON", "off", "on"])
    parser.add_argument(
        "--profiles",
        default=",".join(COMPONENT_PROFILES),
        help="Profil komponen (koma): OFF,ON_FULL,ON_COALESCE_ONLY,...",
    )
    parser.add_argument("--sample-rows", type=int, default=50_000)
    args = parser.parse_args()

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]

    if args.command == "partition-skew":
        out = measure_partition_skew(args.aqe_scenario)
    elif args.command == "components":
        out = measure_components(args.aqe_scenario, profiles=profiles)
    elif args.command == "format":
        out = measure_format_comparison(args.aqe_scenario, sample_rows=args.sample_rows)
    elif args.command == "silver-summary":
        out = measure_silver_summary(args.aqe_scenario)
    else:
        out = {
            "partition_skew": measure_partition_skew(args.aqe_scenario),
            "components": measure_components(args.aqe_scenario, profiles=profiles),
            "format": measure_format_comparison(args.aqe_scenario, sample_rows=args.sample_rows),
            "silver_summary": measure_silver_summary(args.aqe_scenario),
        }

    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
