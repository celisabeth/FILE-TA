"""
Metrik pipeline terpusat — JSON untuk eksperimen metadata & monitoring.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def metrics_dir(path: str | None = None) -> Path:
    if path:
        return Path(path)
    try:
        from benchmark.experiment_run import resolve_metrics_dir

        return resolve_metrics_dir()
    except Exception:
        pass
    env = (
        os.environ.get("INSIGHT_METRICS_DIR")
        or os.environ.get("META_METRICS_DIR")
        or os.environ.get("AQE_METRICS_DIR")
    )
    if env:
        return Path(env)
    if Path("/opt/airflow/metrics").is_dir():
        return Path("/opt/airflow/metrics")
    return Path("metrics")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def persist_pipeline_run_metrics(
    *,
    pipeline: str,
    results: dict[str, Any],
    started_at: datetime,
    ended_at: datetime,
    metrics_dir_path: str | None = None,
    scenario: str | None = None,
    spark_configs: dict[str, str] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Tulis hasil run pipeline ke JSON (staging, silver, gold, AQE, dll.)."""
    out_dir = metrics_dir(metrics_dir_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    sc = (scenario or "default").upper().replace(" ", "_")
    ts = ended_at.strftime("%Y%m%d_%H%M%S")
    suffix = f"_{sc}" if scenario else ""
    path = out_dir / f"{pipeline}{suffix}_{ts}.json"

    duration = (ended_at - started_at).total_seconds()
    written = {k: v for k, v in results.items() if isinstance(v, dict) and v.get("written")}
    payload: dict[str, Any] = {
        "pipeline": pipeline,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_sec": round(duration, 3),
        "summary": {
            "tables_total": len(results),
            "tables_written": len(written) if written else len(results),
            "rows_written": sum(
                int(r.get("row_count", 0))
                for r in results.values()
                if isinstance(r, dict)
            ),
        },
        "tables": results,
    }
    if scenario:
        payload["aqe_scenario"] = scenario
    if spark_configs:
        payload["spark_configs"] = spark_configs
    if extra:
        payload.update(extra)
    payload["metrics_file"] = path.name

    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    try:
        from benchmark.experiment_run import register_artifact

        register_artifact(path.name, role=f"pipeline:{pipeline}")
    except Exception:
        pass

    return path


def latest_metrics_file(
    pipeline: str,
    scenario: str | None = None,
    metrics_dir_path: str | None = None,
) -> Path | None:
    """Ambil file metrik terbaru untuk pipeline (dan skenario opsional)."""
    out_dir = metrics_dir(metrics_dir_path)
    if not out_dir.is_dir():
        return None
    if scenario:
        sc = scenario.upper()
        candidates = sorted(out_dir.glob(f"{pipeline}_*{sc}*.json"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            candidates = sorted(out_dir.glob(f"{pipeline}_aqe_{sc}_*.json"), key=lambda p: p.stat().st_mtime)
    else:
        candidates = sorted(out_dir.glob(f"{pipeline}_*.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None
