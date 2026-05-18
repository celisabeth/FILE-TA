#!/usr/bin/env python3
"""Hitung baris per CSV di data/staging/ — sebelum/sesudah append."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def count_csv(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        return sum(1 for _ in reader)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hitung baris staging CSV")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "staging",
    )
    args = parser.parse_args()
    staging = args.dir
    if not staging.is_dir():
        print(f"Folder tidak ada: {staging}")
        return

    files = sorted(staging.glob("raw_*.csv"))
    if not files:
        print(f"Tidak ada raw_*.csv di {staging}")
        return

    total = 0
    print(f"\n{'File':<32} {'Baris':>12}")
    print("-" * 46)
    for fp in files:
        n = count_csv(fp)
        total += n
        print(f"{fp.name:<32} {n:>12,}")
    print("-" * 46)
    print(f"{'TOTAL':<32} {total:>12,}\n")


if __name__ == "__main__":
    main()
