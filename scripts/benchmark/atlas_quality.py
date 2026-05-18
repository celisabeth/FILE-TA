#!/usr/bin/env python3
"""
Evaluasi kualitas metadata per layer (Bronze / Silver / Gold) dari entitas Atlas.

Logika selaras dengan portal-main/helpers/metadataQualityEvaluator.ts
→ metrics/metadata_quality_*.json (BAB IV §4.1.6).
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
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark._common import metrics_dir, utc_now, write_json

logger = logging.getLogger("benchmark.atlas_quality")

ATLAS_URL = os.environ.get("ATLAS_URL", "http://atlas:21000")
ATLAS_USER = os.environ.get("ATLAS_USER", "admin")
ATLAS_PASS = os.environ.get("ATLAS_PASS", "admin")

EVAL_LAYERS = [
    ("bronze", "Bronze", "Bronze_Layer"),
    ("silver", "Silver", "Silver_Layer"),
    ("gold", "Gold", "Gold_Layer"),
]

METHODOLOGY = (
    "Skor dihitung dari rata-rata entitas lakehouse_dataset per layer di Atlas: "
    "Completeness = kelengkapan atribut wajib; Accuracy = validitas skema/profil kualitas; "
    "Timeliness = kesegaran ingested_at/enriched_at; Consistency = keselarasan layer, "
    "qualifiedName, lokasi, dan klasifikasi. Skala 1–5 = pembulatan skor % ÷ 20."
)


def _auth_header() -> str:
    token = base64.b64encode(f"{ATLAS_USER}:{ATLAS_PASS}".encode()).decode()
    return f"Basic {token}"


def _atlas_post(path: str, body: dict) -> dict:
    url = f"{ATLAS_URL.rstrip('/')}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": _auth_header()},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _parse_json(raw: Any) -> dict:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            val = json.loads(raw)
            return val if isinstance(val, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _filled(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, (int, float)):
        return not (isinstance(val, float) and val != val)
    if isinstance(val, str):
        t = val.strip()
        return bool(t) and t not in ("{}", "[]", "null")
    if isinstance(val, (list, dict)):
        return len(val) > 0
    return True


def _pct_to_score15(pct: float) -> int:
    return min(5, max(1, round(pct / 20) or 1))


def _avg(nums: list[float]) -> float:
    return sum(nums) / len(nums) if nums else 0.0


def _layer_from_qn(qn: str, attrs: dict) -> str:
    if attrs.get("layer"):
        return str(attrs["layer"])
    for prefix in ("staging", "bronze", "silver", "gold"):
        if qn.startswith(f"{prefix}."):
            return prefix
    return "unknown"


def _parse_timestamp(attrs: dict) -> float | None:
    raw = attrs.get("enriched_at") or attrs.get("ingested_at")
    if not raw:
        return None
    try:
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return ts.timestamp()
    except ValueError:
        return None


def _score_timeliness(attrs: dict) -> int:
    ts = _parse_timestamp(attrs)
    if not ts:
        return 0
    age_days = (datetime.now(timezone.utc).timestamp() - ts) / 86400
    if age_days <= 7:
        return 100
    if age_days <= 30:
        return 90
    if age_days <= 90:
        return 75
    if age_days <= 180:
        return 60
    return 40


def _completeness_checks(layer: str, attrs: dict, profiling: dict) -> list[bool]:
    business = profiling.get("business") or {}
    quality = profiling.get("quality") or {}
    schema = _parse_json(attrs.get("schema_def"))

    base = [
        _filled(attrs.get("qualifiedName")),
        _filled(attrs.get("name")),
        _filled(attrs.get("description")),
        _filled(attrs.get("layer")),
        _filled(attrs.get("format")),
        _filled(attrs.get("location")),
        len(schema) > 0,
        attrs.get("row_count") is not None,
        _filled(attrs.get("ingested_at")) or _filled(attrs.get("enriched_at")),
    ]

    if layer == "bronze":
        return base

    if layer == "silver":
        return base + [
            _filled(business.get("owner")),
            _filled(business.get("glossary_terms")),
            len(quality) > 0,
            _filled(profiling.get("compliance")),
        ]

    star = profiling.get("star_schema") or {}
    kpi = profiling.get("kpi") or {}
    return base + [
        _filled(star.get("table_type")) or _filled(kpi.get("iku_code")),
        _filled(profiling.get("consumption")),
        _filled(attrs.get("enriched_at")),
    ]


def _score_completeness(layer: str, attrs: dict, profiling: dict) -> int:
    checks = _completeness_checks(layer, attrs, profiling)
    passed = sum(1 for c in checks if c)
    return round(passed / len(checks) * 100) if checks else 0


def _score_accuracy(layer: str, attrs: dict, profiling: dict) -> int:
    schema = _parse_json(attrs.get("schema_def"))
    if not schema:
        return 0
    row_count = attrs.get("row_count")
    if row_count is not None and int(row_count) < 0:
        return 0

    if layer == "bronze":
        return 95

    quality = profiling.get("quality") or {}
    q_score = (
        quality.get("overall_score")
        or quality.get("source_score")
        or quality.get("score")
        or quality.get("quality_score")
    )
    if isinstance(q_score, (int, float)):
        return min(100, max(0, round(float(q_score))))
    if quality.get("source_status") == "PASS":
        return 90
    if quality.get("source_status") == "QUARANTINE":
        return 70

    if layer == "silver":
        return 85

    star = profiling.get("star_schema") or {}
    kpi = profiling.get("kpi") or {}
    if _filled(star.get("table_type")) or _filled(kpi.get("iku_code")):
        return 92
    return 75


def _score_consistency(layer: str, attrs: dict, classifications: list) -> int:
    qn = str(attrs.get("qualifiedName") or "")
    type_names = {c.get("typeName") for c in classifications if c.get("typeName")}
    expected_tag = f"{layer.capitalize()}_Layer"
    loc = str(attrs.get("location") or "").lower()

    checks = [
        str(attrs.get("layer") or "") == layer,
        _layer_from_qn(qn, attrs) == layer,
        qn.startswith(f"{layer}."),
        expected_tag in type_names,
        layer in loc or f"/{layer}/" in loc,
    ]
    passed = sum(1 for c in checks if c)
    return round(passed / len(checks) * 100) if checks else 0


def _evaluate_entity(layer: str, entity: dict) -> dict[str, int]:
    attrs = entity.get("attributes") or {}
    profiling = _parse_json(attrs.get("profiling"))
    classifications = entity.get("classifications") or []
    return {
        "completeness": _score_completeness(layer, attrs, profiling),
        "accuracy": _score_accuracy(layer, attrs, profiling),
        "timeliness": _score_timeliness(attrs),
        "consistency": _score_consistency(layer, attrs, classifications),
    }


def _search_entities(classification: str, limit: int = 200) -> list[dict]:
    body = {
        "typeName": "lakehouse_dataset",
        "classification": classification,
        "excludeDeletedEntities": True,
        "limit": limit,
    }
    try:
        result = _atlas_post("/api/atlas/v2/search/basic", body)
        return result.get("entities") or []
    except urllib.error.URLError as exc:
        logger.warning("Atlas search failed (%s): %s", classification, exc)
        return []


def _aggregate_layer(layer: str, label: str, entities: list[dict]) -> dict:
    if not entities:
        return {
            "layer": layer,
            "label": label,
            "entity_count": 0,
            "completeness": 0,
            "accuracy": 0,
            "timeliness": 0,
            "consistency": 0,
            "completeness_score_1_5": 1,
            "accuracy_score_1_5": 1,
            "timeliness_score_1_5": 1,
            "consistency_score_1_5": 1,
        }

    scores = [_evaluate_entity(layer, e) for e in entities]
    completeness = round(_avg([s["completeness"] for s in scores]))
    accuracy = round(_avg([s["accuracy"] for s in scores]))
    timeliness = round(_avg([s["timeliness"] for s in scores]))
    consistency = round(_avg([s["consistency"] for s in scores]))

    return {
        "layer": layer,
        "label": label,
        "entity_count": len(entities),
        "completeness": completeness,
        "accuracy": accuracy,
        "timeliness": timeliness,
        "consistency": consistency,
        "completeness_score_1_5": _pct_to_score15(completeness),
        "accuracy_score_1_5": _pct_to_score15(accuracy),
        "timeliness_score_1_5": _pct_to_score15(timeliness),
        "consistency_score_1_5": _pct_to_score15(consistency),
    }


def evaluate_metadata_quality() -> dict:
    layers = []
    for layer, label, classification in EVAL_LAYERS:
        entities = _search_entities(classification)
        layers.append(_aggregate_layer(layer, label, entities))

    return {
        "generated_at": utc_now().isoformat(),
        "atlas_url": ATLAS_URL,
        "layers": layers,
        "methodology": METHODOLOGY,
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Evaluate metadata quality from Atlas")
    parser.add_argument("--write", action="store_true", help="Tulis ke metrics/")
    args = parser.parse_args()

    report = evaluate_metadata_quality()
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)

    if args.write:
        ts = utc_now().strftime("%Y%m%d_%H%M%S")
        out = metrics_dir() / f"metadata_quality_{ts}.json"
        write_json(out, report)
        write_json(metrics_dir() / "metadata_quality_latest.json", report)
        logger.info("Metadata quality → %s", out)


if __name__ == "__main__":
    main()
