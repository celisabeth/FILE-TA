#!/usr/bin/env python3
"""Snapshot UMT (Unified Metadata Table) ke metrics/umt_*.json."""

from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from atlas.build_umt import build_umt
from benchmark._common import metrics_dir, utc_now, write_json

logger = logging.getLogger("benchmark.collect_umt")


def collect_umt(limit: int = 500) -> dict:
    return build_umt(limit)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Collect UMT snapshot to metrics/")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    payload = collect_umt(args.limit)
    if args.write:
        ts = utc_now().strftime("%Y%m%d_%H%M%S")
        out = metrics_dir() / f"umt_{ts}.json"
        write_json(out, payload)
        write_json(metrics_dir() / "umt_latest.json", payload)
        logger.info("UMT snapshot → %s (%d rows)", out, len(payload.get("rows", [])))


if __name__ == "__main__":
    main()
