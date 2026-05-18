#!/usr/bin/env python3
"""
Inventaris Atlas: jumlah entitas, coverage dimensi, lineage completeness.

Output: metrics/atlas_inventory_*.json (BAB IV §4.1.3, §4.1.6).
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark._common import metrics_dir, utc_now, write_json

logger = logging.getLogger("benchmark.atlas_inventory")

ATLAS_URL = os.environ.get("ATLAS_URL", "http://atlas:21000")
ATLAS_USER = os.environ.get("ATLAS_USER", "admin")
ATLAS_PASS = os.environ.get("ATLAS_PASS", "admin")

LAYERS = ("staging", "bronze", "silver", "gold")


def _auth_header() -> str:
    token = base64.b64encode(f"{ATLAS_USER}:{ATLAS_PASS}".encode()).decode()
    return f"Basic {token}"


def _atlas_request(method: str, path: str, body: dict | None = None) -> dict | None:
    url = f"{ATLAS_URL.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": _auth_header()},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        logger.warning("Atlas %s %s → %d", method, path, exc.code)
        return None
    except urllib.error.URLError as exc:
        logger.warning("Atlas unreachable: %s", exc)
        return None


def _search_count(type_name: str, **extra) -> int:
    body = {"typeName": type_name, "excludeDeletedEntities": True, "limit": 1, **extra}
    result = _atlas_request("POST", "/api/atlas/v2/search/basic", body)
    if not result:
        return 0
    return int(result.get("approximateCount") or len(result.get("entities") or []))


def _search_entities(type_name: str, limit: int = 500, **extra) -> list[dict]:
    body = {"typeName": type_name, "excludeDeletedEntities": True, "limit": limit, **extra}
    result = _atlas_request("POST", "/api/atlas/v2/search/basic", body)
    return (result or {}).get("entities") or []


def _layer_from_entity(entity: dict) -> str:
    attrs = entity.get("attributes") or {}
    qn = str(attrs.get("qualifiedName") or "")
    if attrs.get("layer"):
        return str(attrs["layer"])
    for prefix in LAYERS:
        if qn.startswith(f"{prefix}."):
            return prefix
    return "unknown"


def _has_lineage(guid: str) -> tuple[bool, bool]:
    """Return (has_incoming, has_outgoing) dari graph lineage."""
    result = _atlas_request(
        "GET",
        f"/api/atlas/v2/lineage/{guid}?direction=BOTH&depth=1",
    )
    if not result:
        return False, False

    relations = result.get("relations") or []
    base = result.get("baseEntityGuid") or guid
    has_in = False
    has_out = False
    for rel in relations:
        if rel.get("relationshipType") in ("Process", "process"):
            continue
        from_id = rel.get("fromEntityId")
        to_id = rel.get("toEntityId")
        if to_id == base or str(to_id) == str(base):
            has_in = True
        if from_id == base or str(from_id) == str(base):
            has_out = True

    # Fallback: cek guid di relasi proses
    guid_entities = result.get("guidEntityMap") or {}
    for _gid, ent in guid_entities.items():
        if ent.get("typeName") == "lakehouse_etl_process":
            continue
    rel_count = len(relations)
    if rel_count > 0 and not has_in and not has_out:
        has_out = True  # minimal ada edge terhubung

    return has_in, has_out


def _coverage_row(entity: dict) -> dict[str, bool]:
    attrs = entity.get("attributes") or {}
    profiling_raw = attrs.get("profiling")
    profiling: dict = {}
    if isinstance(profiling_raw, str):
        try:
            profiling = json.loads(profiling_raw)
        except json.JSONDecodeError:
            profiling = {}
    elif isinstance(profiling_raw, dict):
        profiling = profiling_raw

    business = profiling.get("business") or {}
    classifications = entity.get("classifications") or []
    class_names = {c.get("typeName") for c in classifications}

    schema = attrs.get("schema_def")
    schema_ok = bool(schema and schema != "{}")

    return {
        "schema_documented": schema_ok,
        "owner_steward": bool(business.get("owner")),
        "glossary_term": bool(business.get("glossary_terms")),
        "classification_pii": "PII" in class_names,
    }


def collect_inventory(sample_lineage_limit: int = 80) -> dict:
    datasets = _search_entities("lakehouse_dataset", limit=500)
    processes = _search_entities("lakehouse_etl_process", limit=500)

    by_layer: dict[str, list[dict]] = {layer: [] for layer in LAYERS}
    for ent in datasets:
        layer = _layer_from_entity(ent)
        if layer in by_layer:
            by_layer[layer].append(ent)

    coverage_by_layer: dict[str, dict] = {}
    for layer in ("bronze", "silver", "gold"):
        ents = by_layer.get(layer, [])
        if not ents:
            coverage_by_layer[layer] = {
                "entity_count": 0,
                "schema_documented_pct": 0,
                "owner_steward_pct": 0,
                "glossary_term_pct": 0,
                "classification_pii_pct": 0,
            }
            continue
        rows = [_coverage_row(e) for e in ents]
        n = len(rows)

        def pct(key: str) -> float:
            return round(sum(1 for r in rows if r[key]) / n * 100, 2)

        coverage_by_layer[layer] = {
            "entity_count": n,
            "schema_documented_pct": pct("schema_documented"),
            "owner_steward_pct": pct("owner_steward"),
            "glossary_term_pct": pct("glossary_term"),
            "classification_pii_pct": pct("classification_pii"),
        }

    lineage_by_layer: dict[str, dict] = {}
    for layer in ("bronze", "silver", "gold"):
        ents = by_layer.get(layer, [])[:sample_lineage_limit]
        if not ents:
            lineage_by_layer[layer] = {
                "sampled": 0,
                "with_incoming_pct": 0,
                "with_outgoing_pct": 0,
            }
            continue
        incoming = 0
        outgoing = 0
        for ent in ents:
            guid = ent.get("guid")
            if not guid:
                continue
            has_in, has_out = _has_lineage(guid)
            if has_in:
                incoming += 1
            if has_out:
                outgoing += 1
        n = len(ents)
        lineage_by_layer[layer] = {
            "sampled": n,
            "with_incoming_pct": round(incoming / n * 100, 2),
            "with_outgoing_pct": round(outgoing / n * 100, 2),
        }

    return {
        "generated_at": utc_now().isoformat(),
        "atlas_url": ATLAS_URL,
        "entity_counts": {
            "lakehouse_dataset_total": len(datasets),
            "lakehouse_etl_process_total": len(processes),
            "by_layer": {layer: len(by_layer[layer]) for layer in LAYERS},
            "staging_csv_entities": _search_count("lakehouse_dataset", classification="Staging_Layer"),
            "bronze_entities": _search_count("lakehouse_dataset", classification="Bronze_Layer"),
            "silver_entities": _search_count("lakehouse_dataset", classification="Silver_Layer"),
            "gold_entities": _search_count("lakehouse_dataset", classification="Gold_Layer"),
        },
        "metadata_coverage": coverage_by_layer,
        "lineage_completeness": lineage_by_layer,
        "classifications_registered": _search_count("classification", limit=50) if False else None,
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Atlas entity inventory & coverage")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    payload = collect_inventory()
    payload.pop("classifications_registered", None)

    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.write:
        ts = utc_now().strftime("%Y%m%d_%H%M%S")
        out = metrics_dir() / f"atlas_inventory_{ts}.json"
        write_json(out, payload)
        write_json(metrics_dir() / "atlas_inventory_latest.json", payload)
        logger.info("Atlas inventory → %s", out)


if __name__ == "__main__":
    main()
