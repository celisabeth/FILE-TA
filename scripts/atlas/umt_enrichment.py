"""
Pelengkap baris UMT — isi celah dari dataset_summary, baris layer lain, dan default domain.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("atlas.umt_enrichment")

DEFAULT_DOMAIN = "ITERA Data Lakehouse"

LAYER_BUSINESS_DEFAULTS: dict[str, dict[str, str]] = {
    "staging": {
        "owner": "Tim Data Ingestion",
        "update_frequency": "batch (per upload CSV)",
    },
    "bronze": {
        "owner": "data-platform",
        "update_frequency": "batch",
    },
    "silver": {
        "owner": "data-governance",
        "update_frequency": "batch",
    },
    "gold": {
        "owner": "Biro Akademik & Perencanaan",
        "update_frequency": "harian (OLAP refresh)",
    },
}


def table_name_from_qn(qualified_name: str) -> str:
    if not qualified_name:
        return ""
    base = qualified_name.split("@", 1)[0]
    if "." in base:
        return base.split(".", 1)[1]
    return base


def _is_empty(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, (list, dict)) and len(val) == 0:
        return True
    if isinstance(val, (int, float)) and val == 0:
        return False
    if isinstance(val, str) and not val.strip():
        return True
    return False


def _filled(val: Any) -> bool:
    return not _is_empty(val)


def load_dataset_summary_index(metrics_root: Path | None = None) -> dict[str, dict[str, Any]]:
    """Indeks table_name → ringkasan CSV staging dari metrics/dataset_summary_*.json."""
    try:
        from benchmark._common import metrics_dir

        root = metrics_root or metrics_dir()
    except Exception:
        root = Path("/opt/airflow/metrics") if Path("/opt/airflow/metrics").is_dir() else Path("metrics")

    candidates: list[Path] = []
    for pattern in ("dataset_summary_*.json",):
        candidates.extend(root.glob(pattern))
        runs = root / "runs"
        if runs.is_dir():
            for run_dir in runs.iterdir():
                if run_dir.is_dir():
                    candidates.extend(run_dir.glob(pattern))

    if not candidates:
        return {}

    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read dataset summary %s: %s", latest, exc)
        return {}

    index: dict[str, dict[str, Any]] = {}
    for row in payload.get("tables") or []:
        name = str(row.get("table_name") or "")
        if name:
            index[name] = row
    logger.info("Dataset summary index: %d tables from %s", len(index), latest.name)
    return index


def _merge_technical(target: dict, source: dict) -> None:
    for key in ("schema", "format", "location", "row_count", "column_count", "pii_columns"):
        if _is_empty(target.get(key)) and _filled(source.get(key)):
            target[key] = source[key]


def _merge_business(target: dict, source: dict) -> None:
    for key in (
        "description",
        "owner",
        "domain",
        "glossary_terms",
        "iku_relevance",
        "update_frequency",
        "kpi",
        "consumption",
        "ai_metadata",
    ):
        if _is_empty(target.get(key)) and _filled(source.get(key)):
            target[key] = source[key]


def _merge_operational(target: dict, source: dict) -> None:
    for key in ("classifications", "quality", "compliance", "star_schema", "transformations"):
        if _is_empty(target.get(key)) and _filled(source.get(key)):
            target[key] = source[key]


def enrich_umt_rows(
    rows: list[dict],
    *,
    dataset_summary: dict[str, dict[str, Any]] | None = None,
) -> list[dict]:
    """Isi field UMT yang masih null/kosong dari sumber lain dalam run yang sama."""
    ds_index = dataset_summary if dataset_summary is not None else load_dataset_summary_index()

    by_layer_table: dict[tuple[str, str], dict] = {}
    for row in rows:
        table = table_name_from_qn(str(row.get("asset_qualified_name") or ""))
        layer = str(row.get("layer") or "")
        if table and layer:
            by_layer_table[(layer, table)] = row

    for row in rows:
        layer = str(row.get("layer") or "")
        table = table_name_from_qn(str(row.get("asset_qualified_name") or ""))
        tech = row.setdefault("technical_json", {})
        biz = row.setdefault("business_json", {})
        ops = row.setdefault("operational_json", {})

        # Staging: row_count / column_count dari dataset_summary atau bronze bersaudara
        if layer == "staging" and table:
            ds = ds_index.get(table)
            if ds:
                if _is_empty(tech.get("row_count")) and ds.get("row_count") is not None:
                    tech["row_count"] = int(ds["row_count"])
                if _is_empty(tech.get("column_count")) and ds.get("column_count") is not None:
                    tech["column_count"] = int(ds["column_count"])
                elif _is_empty(tech.get("column_count")) and ds.get("row_count") is not None:
                    pass
                if _is_empty(tech.get("location")) and ds.get("file"):
                    tech["location"] = f"s3a://staging/{ds['file']}"
                if _is_empty(tech.get("format")):
                    tech["format"] = "csv"

            bronze_row = by_layer_table.get(("bronze", table))
            if bronze_row:
                _merge_technical(tech, bronze_row.get("technical_json") or {})
                if _is_empty(tech.get("column_count")) and tech.get("schema"):
                    tech["column_count"] = len(tech["schema"])

        # Silver bisa melengkapi dari bronze (nama tabel raw_* vs silver_*)
        if layer == "silver" and table.startswith("silver_"):
            bronze_guess = table.replace("silver_", "raw_", 1)
            bronze_row = by_layer_table.get(("bronze", bronze_guess))
            if bronze_row:
                _merge_technical(tech, bronze_row.get("technical_json") or {})

        # Default bisnis per layer
        defaults = LAYER_BUSINESS_DEFAULTS.get(layer, {})
        if _is_empty(biz.get("domain")):
            biz["domain"] = DEFAULT_DOMAIN
        if _is_empty(biz.get("owner")) and defaults.get("owner"):
            biz["owner"] = defaults["owner"]
        if _is_empty(biz.get("update_frequency")) and defaults.get("update_frequency"):
            biz["update_frequency"] = defaults["update_frequency"]

        for list_key in ("glossary_terms", "iku_relevance"):
            if biz.get(list_key) is None:
                biz[list_key] = []

        if biz.get("kpi") is None and layer == "gold":
            biz["kpi"] = {}
        if biz.get("consumption") is None and layer == "gold":
            biz["consumption"] = {}
        if biz.get("ai_metadata") is None and layer == "gold":
            biz["ai_metadata"] = {}

        if ops.get("classifications") is None:
            ops["classifications"] = []

        # last_enriched_at
        if _is_empty(row.get("last_enriched_at")):
            for candidate in (
                biz.get("enriched_at"),
                tech.get("profiled_at"),
            ):
                if candidate:
                    row["last_enriched_at"] = str(candidate)
                    break
            if _is_empty(row.get("last_enriched_at")) and layer in ("bronze", "silver", "gold"):
                prof = biz.get("profiled_at")
                if prof:
                    row["last_enriched_at"] = str(prof)

    return rows
