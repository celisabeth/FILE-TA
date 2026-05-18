"""Utilitas bersama modul benchmark metadata."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def metrics_dir() -> Path:
    """Direktori metrik: di Docker Airflow = /opt/airflow/metrics (volume ./metrics)."""
    env = (
        os.environ.get("INSIGHT_METRICS_DIR")
        or os.environ.get("META_METRICS_DIR")
        or os.environ.get("AQE_METRICS_DIR")
    )
    if env:
        d = Path(env)
    elif Path("/opt/airflow/metrics").is_dir():
        d = Path("/opt/airflow/metrics")
    else:
        d = Path("metrics")
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o1777)
    except OSError:
        pass
    return d


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    out = path if path.is_absolute() else metrics_dir() / path.name
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        out.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    except PermissionError as exc:
        raise PermissionError(
            f"Tidak bisa menulis {out}. Di host jalankan: mkdir -p metrics && chmod 1777 metrics"
        ) from exc
    return out


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
