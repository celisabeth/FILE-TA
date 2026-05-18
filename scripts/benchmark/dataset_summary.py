#!/usr/bin/env python3
"""Ringkasan dataset staging → metrics/dataset_summary_*.json (BAB III §3.3)."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark._common import metrics_dir, utc_now, write_json

DEFAULT_STAGING = os.environ.get(
    "STAGING_DATA_DIR",
    "/opt/airflow/data/staging"
    if Path("/opt/airflow/data/staging").is_dir()
    else os.path.join(os.path.dirname(__file__), "../../data/staging"),
)


def _count_csv_rows(csv_path: Path) -> int:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        return sum(1 for _ in reader)


def summarize_staging(staging_dir: Path) -> dict:
    tables = []
    total_rows = 0
    total_bytes = 0

    for csv_path in sorted(staging_dir.glob("*.csv")):
        size = csv_path.stat().st_size
        n = _count_csv_rows(csv_path)
        total_rows += n
        total_bytes += size
        tables.append({
            "file": csv_path.name,
            "table_name": csv_path.stem,
            "row_count": n,
            "size_bytes": size,
            "size_mb": round(size / (1024**2), 2),
        })

    return {
        "staging_dir": str(staging_dir.resolve()),
        "generated_at": utc_now().isoformat(),
        "summary": {
            "table_count": len(tables),
            "total_rows": total_rows,
            "total_size_mb": round(total_bytes / (1024**2), 2),
        },
        "tables": tables,
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize staging CSV dataset")
    parser.add_argument("--staging-dir", default=DEFAULT_STAGING)
    args = parser.parse_args()

    staging = Path(args.staging_dir)
    if not staging.is_dir():
        raise SystemExit(f"Staging directory not found: {staging}")

    payload = summarize_staging(staging)
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    out = metrics_dir() / f"dataset_summary_{ts}.json"
    write_json(out, payload)
    print(f"Dataset summary → {out}")


if __name__ == "__main__":
    main()
