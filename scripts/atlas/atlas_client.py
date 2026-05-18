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


def fetch_entity_by_guid(guid: str) -> dict | None:
    result = atlas_request("GET", f"/api/atlas/v2/entity/guid/{guid}?minExtInfo=false&ignoreRelationships=true")
    if not result:
        return None
    return result.get("entity") or result


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
