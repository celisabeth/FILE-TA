#!/usr/bin/env python3
"""
Unified Metadata Table (UMT) — agregasi entitas lakehouse_dataset dari Apache Atlas.

Kolom (view logis §4.1.4):
  asset_qualified_name, layer, technical_json, business_json, operational_json, last_enriched_at

Usage:
  python build_umt.py
  python build_umt.py --output /tmp/umt.json
  ATLAS_URL=http://localhost:22100 python build_umt.py
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from atlas.atlas_client import ATLAS_URL, normalize_dataset_attributes, parse_json_field, search_entities
from atlas.umt_enrichment import enrich_umt_rows

logger = logging.getLogger("build_umt")

LAYER_ORDER = ("staging", "bronze", "silver", "gold", "unknown")


def _layer_from_qn(qn: str, attrs: dict) -> str:
    if attrs.get("layer"):
        return str(attrs["layer"])
    for prefix in ("staging", "bronze", "silver", "gold"):
        if qn.startswith(f"{prefix}."):
            return prefix
    return "unknown"


def _technical_json(attrs: dict) -> dict:
    pii = attrs.get("pii_columns")
    if isinstance(pii, str):
        try:
            pii = json.loads(pii)
        except json.JSONDecodeError:
            pii = []
    return {
        "schema": parse_json_field(attrs.get("schema_def")),
        "format": attrs.get("format"),
        "location": attrs.get("location"),
        "row_count": attrs.get("row_count"),
        "column_count": attrs.get("column_count"),
        "pii_columns": pii if isinstance(pii, list) else [],
    }


def _business_json(attrs: dict) -> dict:
    profiling = parse_json_field(attrs.get("profiling"))
    business = profiling.get("business") or {}
    return {
        "description": attrs.get("description"),
        "owner": business.get("owner"),
        "domain": business.get("domain") or attrs.get("domain"),
        "glossary_terms": business.get("glossary_terms") or [],
        "iku_relevance": business.get("iku_relevance") or [],
        "update_frequency": business.get("update_frequency"),
        "kpi": profiling.get("kpi"),
        "consumption": profiling.get("consumption"),
        "ai_metadata": profiling.get("ai_metadata"),
    }


def _operational_json(attrs: dict, classifications: list) -> dict:
    profiling = parse_json_field(attrs.get("profiling"))
    return {
        "classifications": [c.get("typeName") for c in classifications if c.get("typeName")],
        "quality": profiling.get("quality"),
        "compliance": profiling.get("compliance"),
        "star_schema": profiling.get("star_schema"),
        "transformations": profiling.get("transformations"),
    }


def _last_enriched_at(attrs: dict, layer: str) -> str | None:
    if attrs.get("enriched_at"):
        return str(attrs["enriched_at"])
    if attrs.get("ingested_at"):
        return str(attrs["ingested_at"])
    profiling = parse_json_field(attrs.get("profiling"))
    if profiling.get("profiled_at"):
        return str(profiling["profiled_at"])
    return None


def entity_to_umt_row(entity: dict) -> dict:
    attrs = normalize_dataset_attributes(entity.get("attributes"))
    qn = str(attrs.get("qualifiedName") or "")
    layer = _layer_from_qn(qn, attrs)
    classifications = entity.get("classifications") or []

    return {
        "asset_qualified_name": qn,
        "guid": entity.get("guid"),
        "layer": layer,
        "technical_json": _technical_json(attrs),
        "business_json": _business_json(attrs),
        "operational_json": _operational_json(attrs, classifications),
        "last_enriched_at": _last_enriched_at(attrs, layer),
    }


def fetch_all_datasets(limit: int = 500) -> list[dict]:
    return search_entities("lakehouse_dataset", limit=limit, hydrate=True)


def build_umt(limit: int = 500) -> dict:
    entities = fetch_all_datasets(limit)
    rows = enrich_umt_rows([entity_to_umt_row(e) for e in entities])
    rows.sort(
        key=lambda r: (
            LAYER_ORDER.index(r["layer"]) if r["layer"] in LAYER_ORDER else 99,
            r["asset_qualified_name"],
        )
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "approximate_count": len(rows),
        "rows": rows,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Build Unified Metadata Table from Atlas")
    parser.add_argument("--output", "-o", help="Write JSON snapshot to file")
    parser.add_argument("--limit", type=int, default=500, help="Max entities to fetch")
    args = parser.parse_args()

    logger.info("Atlas: %s | limit=%d", ATLAS_URL, args.limit)
    payload = build_umt(args.limit)
    logger.info("UMT rows: %d", len(payload["rows"]))

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("Written to %s", args.output)
    else:
        print(text)


if __name__ == "__main__":
    main()
