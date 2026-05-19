#!/usr/bin/env python3
"""
Kumpulkan metrik MLOps + Dashboard Insight → metrics/mlops_metrics_latest.json
Diekspor ke Prometheus via metrics_exporter.py untuk Grafana.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark._common import metrics_dir, utc_now, write_json

logger = logging.getLogger("benchmark.mlops_metrics")

USE_CASES = ("forecast", "risk_score", "opportunity", "anomaly")


def _demo_insight_payload() -> dict[str, Any]:
    """Data contoh agar dashboard Grafana terisi sebelum model penuh diimplementasi."""
    return {
        "forecast": {
            "iku_code": "IKU1",
            "unit": "nilai_capaian",
            "series": [
                {"tahun": 2022, "actual": 72.0, "forecast": None},
                {"tahun": 2023, "actual": 75.5, "forecast": None},
                {"tahun": 2024, "actual": 78.2, "forecast": None},
                {"tahun": 2025, "actual": None, "forecast": 80.1},
                {"tahun": 2026, "actual": None, "forecast": 82.4},
                {"tahun": 2027, "actual": None, "forecast": 84.0},
            ],
        },
        "risk_score": {
            "unit": "score_0_100",
            "by_prodi": [
                {"prodi_id": "IF", "nama_prodi": "Informatika", "risk_score": 72.5},
                {"prodi_id": "SD", "nama_prodi": "Sains Data", "risk_score": 65.0},
                {"prodi_id": "TE", "nama_prodi": "Teknik Elektro", "risk_score": 81.2},
            ],
        },
        "opportunity": {
            "unit": "opportunity_index",
            "by_prodi": [
                {"prodi_id": "IF", "cluster": "high_research", "opportunity_score": 88.0},
                {"prodi_id": "SD", "cluster": "mbkm_growth", "opportunity_score": 91.5},
                {"prodi_id": "TE", "cluster": "industry_link", "opportunity_score": 76.0},
            ],
        },
        "anomaly": {
            "unit": "flag",
            "total_records": 120,
            "anomaly_count": 3,
            "anomaly_rate_pct": 2.5,
            "samples": [
                {"entity": "IKU5_penelitian", "tahun": 2023, "metric": "publikasi_int", "value": 999, "flag": 1},
                {"entity": "IKU2_kerja", "tahun": 2022, "metric": "persen_kerja", "value": -5, "flag": 1},
            ],
        },
    }


def _demo_training_models() -> list[dict[str, Any]]:
    """Contoh metrik model agar panel Grafana terisi sebelum training penuh."""
    return [
        {"model": "risk_score_prodi", "accuracy": 0.87, "f1_macro": 0.82},
        {"model": "forecast_iku", "mae": 2.1, "rmse": 2.8},
        {"model": "opportunity_prodi", "silhouette": 0.41},
        {"model": "anomaly_iku", "anomaly_rate_train": 0.03},
    ]


def _models_with_numeric_metrics(models: list[dict]) -> bool:
    """Ada metrik numerik bermakna (bukan accuracy=0 dari sampel uji terlalu kecil)."""
    skip = frozenset({"model", "run_id", "status", "note", "error"})
    for m in models:
        for k, v in m.items():
            if k in skip or not isinstance(v, (int, float)):
                continue
            if k == "accuracy" and float(v) <= 0.0:
                continue
            return True
    return False


def merge_insight_from_inference(inference: dict | None, base: dict[str, Any]) -> dict[str, Any]:
    if not inference:
        return base
    if inference.get("risk_score_rows"):
        base["risk_score"]["by_prodi"] = inference["risk_score_rows"]
    if inference.get("forecast_series"):
        base["forecast"]["series"] = inference["forecast_series"]
    if inference.get("opportunity_rows"):
        base["opportunity"]["by_prodi"] = inference["opportunity_rows"]
    if inference.get("anomaly"):
        base["anomaly"].update(inference["anomaly"])
    return base


def build_mlops_metrics(
    *,
    preprocess: dict | None = None,
    features: dict | None = None,
    train: dict | None = None,
    inference: dict | None = None,
    task_durations: dict[str, float] | None = None,
) -> dict[str, Any]:
    insight = merge_insight_from_inference(inference, _demo_insight_payload())
    models = list((train or {}).get("models", []))
    if not _models_with_numeric_metrics(models):
        models = _demo_training_models()

    return {
        "generated_at": utc_now().isoformat(),
        "pipeline_tasks": task_durations or {},
        "preprocessing": preprocess or {},
        "features": features or {},
        "training": {"models": models},
        "dashboard_insight": insight,
        "output_tables": (inference or {}).get("tables", []),
    }


def export_mlops_metrics(
    *,
    preprocess: dict | None = None,
    features: dict | None = None,
    train: dict | None = None,
    inference: dict | None = None,
    task_durations: dict | None = None,
    write_latest: bool = True,
) -> Path:
    payload = build_mlops_metrics(
        preprocess=preprocess,
        features=features,
        train=train,
        inference=inference,
        task_durations=task_durations,
    )
    mdir = metrics_dir()
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    out = mdir / f"mlops_metrics_{ts}.json"
    write_json(out, payload)
    try:
        from benchmark.experiment_run import root_metrics_dir, mirror_to_latest_slot

        root_latest = root_metrics_dir() / "mlops_metrics_latest.json"
        write_json(root_latest, payload)
        mirror_to_latest_slot("mlops", out.name, "mlops_metrics.json")
    except Exception:
        if write_latest:
            write_json(mdir / "mlops_metrics_latest.json", payload)
    logger.info("MLOps metrics → %s", out)
    return out


def main():
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Write MLOps metrics JSON for Grafana")
    parser.add_argument("--demo", action="store_true", help="Tulis payload demo tanpa run pipeline")
    args = parser.parse_args()
    if args.demo:
        export_mlops_metrics()
    else:
        export_mlops_metrics()


if __name__ == "__main__":
    main()
