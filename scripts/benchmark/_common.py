"""Utilitas bersama modul benchmark metadata."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def metrics_dir() -> Path:
    """Direktori metrik aktif: run audit (`metrics/runs/{id}/`) atau root legacy."""
    try:
        from benchmark.experiment_run import resolve_metrics_dir

        d = resolve_metrics_dir()
    except Exception:
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


def write_json(path: Path, payload: dict[str, Any], *, artifact_role: str | None = None) -> Path:
    out = path if path.is_absolute() else metrics_dir() / path.name
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        out.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    except PermissionError as exc:
        raise PermissionError(
            f"Tidak bisa menulis {out}. Di host jalankan: mkdir -p metrics && chmod 1777 metrics"
        ) from exc
    try:
        from benchmark.experiment_run import register_artifact

        register_artifact(out.name, role=artifact_role)
    except Exception:
        pass
    return out


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_latest_metric_file(root: Path, pattern: str) -> Path | None:
    """File metrik terbaru di root, runs/*, atau latest/{track}/."""
    candidates: list[Path] = []
    candidates.extend(root.glob(pattern))
    candidates.extend(root.glob(f"runs/*/{pattern}"))
    latest_root = root / "latest"
    if latest_root.is_dir():
        candidates.extend(latest_root.glob(f"*/{pattern}"))
        for track in ("aqe", "metadata", "mlops"):
            ptr = latest_root / f"{track}.json"
            if not ptr.is_file():
                continue
            try:
                data = json.loads(ptr.read_text(encoding="utf-8"))
                rel = data.get("dir")
                if rel:
                    candidates.extend((root / rel).glob(pattern))
            except (json.JSONDecodeError, OSError):
                continue
    files = [p for p in candidates if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def speedup_pct(baseline_sec: float, comparison_sec: float) -> float | None:
    """Persen perbaikan durasi baseline (AQE OFF) vs comparison (AQE ON). Positif = ON lebih cepat."""
    if baseline_sec is None or comparison_sec is None:
        return None
    base = float(baseline_sec)
    comp = float(comparison_sec)
    if base <= 0:
        return None
    return round((base - comp) / base * 100, 2)


def throughput_rows_per_sec(rows: int, duration_sec: float) -> float | None:
    """Throughput baris per detik; None jika durasi tidak valid."""
    if duration_sec is None:
        return None
    dur = float(duration_sec)
    if dur <= 0:
        return None
    return round(int(rows) / dur, 2)
