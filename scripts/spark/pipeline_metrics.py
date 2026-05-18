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
    return Path(
        path
        or os.environ.get("INSIGHT_METRICS_DIR")
        or os.environ.get("META_METRICS_DIR")
        or os.environ.get("AQE_METRICS_DIR", "/opt/airflow/metrics")
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def persist_pipeline_run_metrics(
    *,
    pipeline: str,
    results: dict[str, Any],
    started_at: datetime,
    ended_at: datetime,
    metrics_dir_path: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Tulis hasil run pipeline ke JSON (staging, silver, gold, dll.)."""
    out_dir = metrics_dir(metrics_dir_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = ended_at.strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"{pipeline}_{ts}.json"

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
    if extra:
        payload.update(extra)

    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path
