#!/usr/bin/env python3
"""
Agregasi semua metrik eksperimen metadata → metrics/experiment_summary_*.json
Untuk laporan BAB IV §4.1.1–4.1.6.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark._common import load_json, metrics_dir, utc_now, write_json

logger = logging.getLogger("benchmark.aggregate")


def _collect_by_glob(directory: Path, pattern: str, max_files: int = 3) -> list[dict]:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
    return [load_json(f) | {"_file": f.name} for f in files[-max_files:]]


def _latest(directory: Path, pattern: str) -> dict | None:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not files:
        return None
    return load_json(files[-1])


def aggregate(
    metrics_path: Path | None = None,
    experiment_id: str | None = None,
    *,
    track: str | None = None,
) -> dict:
    if metrics_path is None:
        try:
            from benchmark.experiment_run import current_run_dir, resolve_metrics_dir

            mdir = current_run_dir(track) or resolve_metrics_dir(track)
        except Exception:
            mdir = metrics_dir()
    else:
        mdir = metrics_path

    quality = _latest(mdir, "metadata_quality_*.json") or _latest(mdir, "metadata_quality_latest.json")
    inventory = _latest(mdir, "atlas_inventory_*.json") or _latest(mdir, "atlas_inventory_latest.json")
    umt = _latest(mdir, "umt_*.json") or _latest(mdir, "umt_latest.json")

    pipelines = {
        "staging_to_bronze": _latest(mdir, "staging_to_bronze_*.json"),
        "bronze_to_silver": _latest(mdir, "bronze_to_silver_*.json"),
        "silver_to_gold": _latest(mdir, "silver_to_gold_*.json"),
    }

    total_pipeline_sec = sum(
        float(p.get("duration_sec", 0))
        for p in pipelines.values()
        if p and p.get("duration_sec")
    )

    run_id = os.environ.get("EXPERIMENT_RUN_ID")
    return {
        "experiment_id": experiment_id or run_id or f"META-EXP-{utc_now().strftime('%Y%m%d-%H%M%S')}",
        "experiment_track": track or os.environ.get("EXPERIMENT_TRACK"),
        "experiment_run_id": run_id,
        "generated_at": utc_now().isoformat(),
        "metrics_directory": str(mdir.resolve()),
        "dataset_summaries": _collect_by_glob(mdir, "dataset_summary_*.json"),
        "pipelines": pipelines,
        "pipeline_runtime_total_sec": round(total_pipeline_sec, 3) if total_pipeline_sec else None,
        "metadata_quality": quality,
        "atlas_inventory": inventory,
        "umt": {
            "approximate_count": (umt or {}).get("approximate_count"),
            "generated_at": (umt or {}).get("generated_at"),
            "_file": "umt_latest.json" if umt else None,
        },
        "registration_snapshots": _collect_by_glob(mdir, "atlas_registration_*.json"),
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Aggregate metadata experiment metrics")
    parser.add_argument("--metrics-dir", default=None)
    parser.add_argument("--experiment-id", default=None)
    parser.add_argument("--write-latest", action="store_true")
    args = parser.parse_args()

    track = os.environ.get("EXPERIMENT_TRACK", "metadata")
    mdir = Path(args.metrics_dir) if args.metrics_dir else metrics_dir()
    summary = aggregate(mdir, experiment_id=args.experiment_id, track=track)
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    out = mdir / f"experiment_summary_{ts}.json"
    write_json(out, summary, artifact_role="experiment_summary")
    if args.write_latest:
        from benchmark.experiment_run import mirror_to_latest_slot

        mirror_to_latest_slot(track, out.name, "experiment_summary.json")
    try:
        from benchmark.experiment_run import finalize_run

        finalize_run(summary_file=out.name)
    except Exception:
        pass
    logger.info("Experiment summary → %s", out)


if __name__ == "__main__":
    main()
