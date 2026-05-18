#!/usr/bin/env python3
"""Daftar run audit metrik (metadata / aqe / mlops) untuk evaluasi per metode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmark.experiment_run import index_path, root_metrics_dir, runs_root


def main() -> None:
    parser = argparse.ArgumentParser(description="List metrics experiment runs")
    parser.add_argument("--track", choices=["metadata", "aqe", "mlops"], default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    idx_path = index_path()
    if idx_path.is_file():
        data = json.loads(idx_path.read_text(encoding="utf-8"))
    else:
        data = {"runs": [], "latest": {}}

    runs = data.get("runs", [])
    if args.track:
        runs = [r for r in runs if r.get("track") == args.track]

    if args.json:
        print(json.dumps({"latest": data.get("latest", {}), "runs": runs}, indent=2))
        return

    print(f"Metrics root: {root_metrics_dir()}")
    print(f"Runs dir:     {runs_root()}")
    print("\nLatest per track:")
    for track, rid in sorted((data.get("latest") or {}).items()):
        print(f"  {track:10} → {rid}")

    print("\nAll runs:")
    for r in runs:
        print(
            f"  {r.get('run_id')}  track={r.get('track')}  "
            f"started={r.get('started_at')}  dag={r.get('dag_id')}"
        )


if __name__ == "__main__":
    main()
