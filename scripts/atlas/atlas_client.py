"""
Klien Atlas bersama — search + hydrate entitas penuh (atribut custom & klasifikasi).

Atlas POST /search/basic sering hanya mengembalikan qualifiedName/description;
evaluasi UMT, kualitas metadata, dan inventaris membutuhkan GET per guid.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger("atlas.client")

ATLAS_URL = os.environ.get("ATLAS_URL", "http://atlas:21000")
ATLAS_USER = os.environ.get("ATLAS_USER", "admin")
ATLAS_PASS = os.environ.get("ATLAS_PASS", "admin")


def _auth_header() -> str:
    token = base64.b64encode(f"{ATLAS_USER}:{ATLAS_PASS}".encode()).decode()
    return f"Basic {token}"


def atlas_request(method: str, path: str, body: dict | None = None, *, timeout: int = 60) -> dict | None:
    url = f"{ATLAS_URL.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": _auth_header()},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        logger.warning("Atlas %s %s → %s", method, path, exc.code)
        return None
    except urllib.error.URLError as exc:
        logger.warning("Atlas unreachable %s: %s", path, exc)
        return None


def normalize_dataset_attributes(attrs: Any) -> dict[str, Any]:
    """Samakan bentuk atribut Atlas (search stub vs GET penuh, alias camelCase)."""
    if not attrs:
        return {}
    if isinstance(attrs, list):
        merged: dict[str, Any] = {}
        for item in attrs:
            if isinstance(item, dict) and item.get("name") is not None:
                merged[str(item["name"])] = item.get("value")
        attrs = merged
    if not isinstance(attrs, dict):
        return {}

    out = dict(attrs)
    aliases: dict[str, tuple[str, ...]] = {
        "row_count": ("rowCount",),
        "column_count": ("columnCount",),
        "schema_def": ("schemaDef", "schema"),
        "pii_columns": ("piiColumns",),
        "ingested_at": ("ingestedAt",),
        "enriched_at": ("enrichedAt",),
        "qualifiedName": ("qualified_name",),
    }
    for canonical, alts in aliases.items():
        if out.get(canonical) is None:
            for alt in alts:
                if out.get(alt) is not None:
                    out[canonical] = out[alt]
                    break
    return out


def parse_json_field(raw: Any) -> dict:
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


def guid_for_qualified_name(qualified_name: str, type_name: str = "lakehouse_dataset") -> str | None:
    path = (
        f"/api/atlas/v2/entity/uniqueAttribute/type/{type_name}"
        f"?attr:qualifiedName={urllib.parse.quote(qualified_name)}"
    )
    result = atlas_request("GET", path)
    if not result:
        return None
    entity = result.get("entity") or result
    return entity.get("guid") if isinstance(entity, dict) else None


def upsert_entity(entity_body: dict, *, type_name: str = "lakehouse_dataset") -> dict | None:
    """POST entitas baru atau PUT jika qualifiedName sudah ada (termasuk setelah HTTP 409)."""
    qn = (entity_body.get("entity") or {}).get("attributes", {}).get("qualifiedName")
    if not qn:
        return atlas_request("POST", "/api/atlas/v2/entity", entity_body)

    guid = guid_for_qualified_name(str(qn), type_name)
    if guid:
        entity_body.setdefault("entity", {})["guid"] = guid
        put = atlas_request("PUT", f"/api/atlas/v2/entity/guid/{guid}", entity_body)
        if put is not None:
            return put

    post = atlas_request("POST", "/api/atlas/v2/entity", entity_body)
    if post is not None:
        return post

    guid = guid_for_qualified_name(str(qn), type_name)
    if not guid:
        return None
    entity_body.setdefault("entity", {})["guid"] = guid
    return atlas_request("PUT", f"/api/atlas/v2/entity/guid/{guid}", entity_body)


def fetch_entity_by_guid(guid: str) -> dict | None:
    result = atlas_request("GET", f"/api/atlas/v2/entity/guid/{guid}?minExtInfo=false&ignoreRelationships=true")
    if not result:
        return None
    entity = result.get("entity") or result
    if isinstance(entity, dict) and entity.get("attributes") is not None:
        entity = dict(entity)
        entity["attributes"] = normalize_dataset_attributes(entity["attributes"])
    return entity


def hydrate_entities(entities: list[dict], *, log_every: int = 0) -> list[dict]:
    """Muat atribut lengkap per guid; gabungkan klasifikasi dari hasil search jika perlu."""
    hydrated: list[dict] = []
    for i, stub in enumerate(entities):
        guid = stub.get("guid")
        if not guid:
            hydrated.append(stub)
            continue
        full = fetch_entity_by_guid(str(guid))
        if not full:
            hydrated.append(stub)
            continue
        if not full.get("classifications") and stub.get("classifications"):
            full["classifications"] = stub["classifications"]
        hydrated.append(full)
        if log_every and (i + 1) % log_every == 0:
            logger.info("Hydrated %d/%d Atlas entities", i + 1, len(entities))
    return hydrated


def search_entities(
    type_name: str,
    *,
    classification: str | None = None,
    limit: int = 500,
    hydrate: bool = True,
) -> list[dict]:
    body: dict[str, Any] = {
        "typeName": type_name,
        "excludeDeletedEntities": True,
        "limit": limit,
        "offset": 0,
    }
    if classification:
        body["classification"] = classification
    result = atlas_request("POST", "/api/atlas/v2/search/basic", body)
    entities = (result or {}).get("entities") or []
    if hydrate and entities:
        logger.info("Hydrating %d %s entities from Atlas", len(entities), type_name)
        return hydrate_entities(entities)
    return entities
