#!/usr/bin/env python3
"""
Orkestrator eksperimen metadata end-to-end.

Alur:
  1. Ringkasan dataset (opsional)
  2. Staging → Bronze + Atlas Bronze
  3. Bronze → Silver + Atlas Silver
  4. Silver → Gold + Atlas Gold
  5. UMT + kualitas metadata + inventaris Atlas
  6. Agregasi experiment_summary

Jalankan dari host (stack Docker harus hidup):
  PYTHONPATH=scripts META_METRICS_DIR=metrics python3 scripts/benchmark/run_experiment.py

Dari container Airflow:
  docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger("benchmark.experiment")


def _step(name: str, fn):
    logger.info("=" * 60)
    logger.info("STEP: %s", name)
    logger.info("=" * 60)
    return fn()


def run_local(
    *,
    skip_dataset: bool = False,
    skip_staging: bool = False,
    staging_dir: str | None = None,
    atlas_url: str | None = None,
) -> None:
    from benchmark._common import metrics_dir, utc_now, write_json
    from benchmark.aggregate_results import aggregate
    from benchmark.atlas_inventory import collect_inventory
    from benchmark.atlas_quality import evaluate_metadata_quality
    from benchmark.atlas_registration_snapshot import write_registration_snapshot
    from benchmark.collect_umt import collect_umt
    from benchmark.dataset_summary import summarize_staging

    if atlas_url:
        os.environ["ATLAS_URL"] = atlas_url

    if not skip_dataset and staging_dir:
        staging = Path(staging_dir)
        if staging.is_dir() and any(staging.glob("*.csv")):
            payload = summarize_staging(staging)
            write_json(metrics_dir() / f"dataset_summary_{utc_now().strftime('%Y%m%d_%H%M%S')}.json", payload)

    if not skip_staging:
        from spark.staging_to_bronze import run_staging_to_bronze

        profiling = _step("staging_to_bronze", run_staging_to_bronze)
        from atlas.register_bronze_metadata import register_all_metadata

        _step(
            "atlas bronze registration",
            lambda: register_all_metadata(profiling_results=profiling),
        )
        write_registration_snapshot("bronze")

    from spark.bronze_to_silver import run_bronze_to_silver
    from spark.silver_to_gold import run_silver_to_gold

    silver_prof = _step("bronze_to_silver", run_bronze_to_silver)
    from atlas.register_silver_metadata import register_all_silver_metadata

    _step(
        "atlas silver registration",
        lambda: register_all_silver_metadata(profiling_results=silver_prof),
    )
    write_registration_snapshot("silver")

    gold_prof = _step("silver_to_gold", run_silver_to_gold)
    from atlas.register_gold_metadata import register_all_gold_metadata

    _step(
        "atlas gold registration",
        lambda: register_all_gold_metadata(profiling_results=gold_prof),
    )
    write_registration_snapshot("gold")

    umt = _step("build UMT", collect_umt)
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    write_json(metrics_dir() / f"umt_{ts}.json", umt)
    write_json(metrics_dir() / "umt_latest.json", umt)

    quality = _step("metadata quality", evaluate_metadata_quality)
    write_json(metrics_dir() / f"metadata_quality_{ts}.json", quality)
    write_json(metrics_dir() / "metadata_quality_latest.json", quality)

    inventory = _step("atlas inventory", collect_inventory)
    write_json(metrics_dir() / f"atlas_inventory_{ts}.json", inventory)
    write_json(metrics_dir() / "atlas_inventory_latest.json", inventory)

    summary = aggregate()
    write_json(metrics_dir() / f"experiment_summary_{ts}.json", summary)
    write_json(metrics_dir() / "experiment_summary_latest.json", summary)
    logger.info("Experiment complete → %s", metrics_dir())


def run_via_airflow(docker_container: str = "lhmeta-airflow-scheduler") -> None:
    cmd = [
        "docker",
        "exec",
        docker_container,
        "airflow",
        "dags",
        "trigger",
        "metadata_full_experiment",
    ]
    logger.info("Triggering Airflow DAG: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="End-to-end metadata experiment orchestrator")
    parser.add_argument("--mode", choices=["local", "airflow"], default="local")
    parser.add_argument("--skip-dataset-summary", action="store_true")
    parser.add_argument("--skip-staging", action="store_true", help="Bronze sudah terisi")
    parser.add_argument(
        "--staging-dir",
        default=os.environ.get("STAGING_DATA_DIR", "data/staging"),
    )
    parser.add_argument("--atlas-url", default=None)
    parser.add_argument("--docker-container", default="lhmeta-airflow-scheduler")
    args = parser.parse_args()

    if args.mode == "airflow":
        run_via_airflow(args.docker_container)
    else:
        run_local(
            skip_dataset=args.skip_dataset_summary,
            skip_staging=args.skip_staging,
            staging_dir=args.staging_dir,
            atlas_url=args.atlas_url,
        )


if __name__ == "__main__":
    main()
