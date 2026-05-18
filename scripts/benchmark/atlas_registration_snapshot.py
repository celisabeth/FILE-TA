#!/usr/bin/env python3
"""Snapshot ringkas setelah registrasi Atlas per layer."""

from __future__ import annotations

import os

from benchmark._common import metrics_dir, utc_now, write_json
from benchmark.atlas_inventory import _search_count


def snapshot_registration(layer: str) -> dict:
    """Catat jumlah entitas Atlas setelah pipeline layer selesai."""
    return {
        "layer": layer,
        "generated_at": utc_now().isoformat(),
        "atlas_url": os.environ.get("ATLAS_URL", "http://atlas:21000"),
        "counts": {
            "lakehouse_dataset": _search_count("lakehouse_dataset"),
            "lakehouse_etl_process": _search_count("lakehouse_etl_process"),
            f"{layer}_classified": _search_count(
                "lakehouse_dataset",
                classification=f"{layer.capitalize()}_Layer",
            ),
        },
    }


def write_registration_snapshot(layer: str) -> str:
    payload = snapshot_registration(layer)
    ts = utc_now().strftime("%Y%m%d_%H%M%S")
    out = metrics_dir() / f"atlas_registration_{layer}_{ts}.json"
    write_json(out, payload)
    return str(out)
