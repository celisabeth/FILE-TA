"""
Skema audit metrik per run eksperimen (metadata / aqe / mlops).

Struktur:
  metrics/
    index.json
    latest/{track}.json          # pointer run terakhir per metode (tidak saling timpa)
    runs/{run_id}/
      manifest.json
      staging_to_bronze_*.json
      experiment_summary.json
      ...

Env (di-set task init_experiment_run):
  EXPERIMENT_TRACK=metadata|aqe|mlops
  EXPERIMENT_RUN_ID=metadata_20260518T120114Z
  EXPERIMENT_RUN_DIR=/opt/airflow/metrics/runs/metadata_20260518T120114Z
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TRACKS = frozenset({"metadata", "aqe", "mlops"})


def root_metrics_dir() -> Path:
    env = (
        os.environ.get("INSIGHT_METRICS_DIR")
        or os.environ.get("META_METRICS_DIR")
        or os.environ.get("AQE_METRICS_DIR")
    )
    if env:
        root = Path(env)
    elif Path("/opt/airflow/metrics").is_dir():
        root = Path("/opt/airflow/metrics")
    else:
        root = Path("metrics")

    try:
        root = root.resolve()
    except OSError:
        root = root.absolute()

    # Hindari folder ganda metrics/metrics/ saat path relatif dipakai dari dalam metrics/
    while root.name == "metrics" and root.parent.name == "metrics":
        root = root.parent
    return root


def runs_root() -> Path:
    return root_metrics_dir() / "runs"


def latest_pointer_path(track: str) -> Path:
    return root_metrics_dir() / "latest" / f"{track}.json"


def index_path() -> Path:
    return root_metrics_dir() / "index.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _load_index() -> dict[str, Any]:
    path = index_path()
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"version": 1, "runs": [], "latest": {}}


def _save_index(data: dict[str, Any]) -> None:
    path = index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def make_run_id(track: str, when: datetime | None = None) -> str:
    t = track.lower().strip()
    if t not in TRACKS:
        raise ValueError(f"track must be one of {sorted(TRACKS)}")
    ts = (when or _utc_now()).strftime("%Y%m%dT%H%M%SZ")
    short = uuid.uuid4().hex[:6]
    return f"{t}_{ts}_{short}"


def begin_run(
    track: str,
    *,
    label: str | None = None,
    dag_id: str | None = None,
    dag_run_id: str | None = None,
    notes: str | None = None,
    run_id: str | None = None,
) -> Path:
    """Buat folder run baru; aktifkan untuk proses ini (env + manifest)."""
    t = track.lower().strip()
    if t not in TRACKS:
        raise ValueError(f"track must be one of {sorted(TRACKS)}")

    rid = run_id or make_run_id(t)
    run_dir = runs_root() / rid
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "run_id": rid,
        "track": t,
        "label": label or rid,
        "dag_id": dag_id,
        "dag_run_id": dag_run_id,
        "notes": notes,
        "started_at": _utc_now().isoformat(),
        "ended_at": None,
        "artifacts": [],
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )

    os.environ["EXPERIMENT_TRACK"] = t
    os.environ["EXPERIMENT_RUN_ID"] = rid
    os.environ["EXPERIMENT_RUN_DIR"] = str(run_dir)
    (runs_root() / f".active_{t}").write_text(rid, encoding="utf-8")

    idx = _load_index()
    idx.setdefault("runs", []).append(
        {
            "run_id": rid,
            "track": t,
            "dir": f"runs/{rid}",
            "started_at": manifest["started_at"],
            "dag_id": dag_id,
            "dag_run_id": dag_run_id,
        }
    )
    idx.setdefault("latest", {})[t] = rid
    _save_index(idx)

    _write_latest_pointer(t, rid, run_dir)
    return run_dir


def _write_latest_pointer(track: str, run_id: str, run_dir: Path) -> None:
    ptr = latest_pointer_path(track)
    ptr.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "track": track,
        "run_id": run_id,
        "dir": str(run_dir.relative_to(root_metrics_dir())),
        "updated_at": _utc_now().isoformat(),
    }
    ptr.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def current_run_dir(track: str | None = None) -> Path | None:
    """Direktori run aktif dari env atau pointer latest per track."""
    env_dir = os.environ.get("EXPERIMENT_RUN_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p

    t = (track or os.environ.get("EXPERIMENT_TRACK") or "").lower()
    if t:
        ptr = latest_pointer_path(t)
        if ptr.is_file():
            data = json.loads(ptr.read_text(encoding="utf-8"))
            rel = data.get("dir")
            if rel:
                candidate = root_metrics_dir() / rel
                if candidate.is_dir():
                    return candidate

    rid = os.environ.get("EXPERIMENT_RUN_ID")
    if rid:
        candidate = runs_root() / rid
        if candidate.is_dir():
            return candidate
    return None


def resolve_metrics_dir(track: str | None = None) -> Path:
    """Target tulis metrik: run folder jika aktif, else root metrics (legacy)."""
    t = (track or os.environ.get("EXPERIMENT_TRACK") or "").lower()
    if t and not os.environ.get("EXPERIMENT_RUN_DIR"):
        active = runs_root() / f".active_{t}"
        if active.is_file():
            rid = active.read_text(encoding="utf-8").strip()
            candidate = runs_root() / rid
            if candidate.is_dir():
                os.environ["EXPERIMENT_TRACK"] = t
                os.environ["EXPERIMENT_RUN_ID"] = rid
                os.environ["EXPERIMENT_RUN_DIR"] = str(candidate)

    run = current_run_dir(track or t or None)
    if run:
        return run
    root = root_metrics_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root


def register_artifact(filename: str, *, role: str | None = None) -> None:
    """Catat file ke manifest.json run aktif; salin dari root jika tertulis di luar run folder."""
    run_dir = current_run_dir()
    if not run_dir:
        return
    dest = run_dir / filename
    if not dest.is_file():
        stray = root_metrics_dir() / filename
        if stray.is_file() and stray.resolve() != dest.resolve():
            dest.write_bytes(stray.read_bytes())
        elif not dest.is_file():
            return

    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = {"file": filename, "recorded_at": _utc_now().isoformat()}
    if role:
        entry["role"] = role
    arts = manifest.setdefault("artifacts", [])
    if not any(a.get("file") == filename for a in arts):
        arts.append(entry)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


def finalize_run(*, summary_file: str | None = None, extra: dict[str, Any] | None = None) -> Path | None:
    """Tutup run: ended_at, optional ringkasan, perbarui index."""
    run_dir = current_run_dir()
    if not run_dir:
        return None

    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ended_at"] = _utc_now().isoformat()
    if summary_file:
        manifest["summary_file"] = summary_file
        register_artifact(summary_file, role="summary")
    if extra:
        manifest["finalize"] = extra
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )

    track = manifest.get("track")
    rid = manifest.get("run_id")
    if track and rid:
        idx = _load_index()
        for row in idx.get("runs", []):
            if row.get("run_id") == rid:
                row["ended_at"] = manifest["ended_at"]
                if summary_file:
                    row["summary_file"] = summary_file
        idx.setdefault("latest", {})[track] = rid
        _save_index(idx)
        _write_latest_pointer(track, rid, run_dir)

    return run_dir


def activate_from_airflow_context(context: dict, track: str) -> Path:
    """Pull run_dir dari task init_experiment_run atau buat run baru."""
    ti = context.get("ti")
    if ti:
        rd = ti.xcom_pull(task_ids="init_experiment_run", key="experiment_run_dir")
        if rd:
            os.environ["EXPERIMENT_RUN_DIR"] = rd
            rid = ti.xcom_pull(task_ids="init_experiment_run", key="experiment_run_id")
            if rid:
                os.environ["EXPERIMENT_RUN_ID"] = rid
            os.environ["EXPERIMENT_TRACK"] = track
            return Path(rd)

    existing = current_run_dir(track)
    if existing:
        return existing

    dag_run = context.get("dag_run")
    return begin_run(
        track,
        dag_id=getattr(dag_run, "dag_id", None) if dag_run else None,
        dag_run_id=getattr(dag_run, "run_id", None) if dag_run else None,
        label=(dag_run.conf.get("label") if dag_run and getattr(dag_run, "conf", None) else None),
    )


def mirror_to_latest_slot(track: str, run_filename: str, latest_basename: str) -> Path | None:
    """Salin artefak dari run aktif ke metrics/latest/{track}/ (tidak timpa metode lain)."""
    run_dir = current_run_dir(track)
    if not run_dir:
        return None
    src = run_dir / run_filename
    if not src.is_file():
        return None
    dest = root_metrics_dir() / "latest" / track / latest_basename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def init_airflow_task(**context) -> str:
    """Callable task init_experiment_run di DAG."""
    params = context.get("params") or {}
    track = (
        params.get("experiment_track")
        if hasattr(params, "get")
        else getattr(params, "experiment_track", None)
    ) or os.environ.get("EXPERIMENT_TRACK", "metadata")
    dag_run = context.get("dag_run")
    conf = getattr(dag_run, "conf", None) or {}
    run_dir = begin_run(
        str(track).lower(),
        label=conf.get("label") if isinstance(conf, dict) else None,
        dag_id=getattr(dag_run, "dag_id", None) if dag_run else None,
        dag_run_id=getattr(dag_run, "run_id", None) if dag_run else None,
        notes=conf.get("notes") if isinstance(conf, dict) else None,
        run_id=conf.get("experiment_run_id") if isinstance(conf, dict) else None,
    )
    context["ti"].xcom_push(key="experiment_run_dir", value=str(run_dir))
    context["ti"].xcom_push(key="experiment_run_id", value=run_dir.name)
    return str(run_dir)
