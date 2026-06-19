#!/usr/bin/env python3
"""
Patch Superset TrinoEngineSpec.get_indexes for Iceberg pseudo-partition metadata.
Applied at Docker build time (not in superset_config — avoids Flask app context error).

Ref: https://github.com/apache/superset/issues/26449
"""
from __future__ import annotations

import sys
from pathlib import Path

TRINO_PY = Path("/app/superset/db_engine_specs/trino.py")

OLD = """        try:
            return super().get_indexes(database, inspector, table_name, schema)
        except NoSuchTableError:
            return []"""

NEW = """        try:
            indexes = super().get_indexes(database, inspector, table_name, schema)
            _iceberg_meta = {"record_count", "file_count", "total_size", "data"}
            if (
                len(indexes) == 1
                and indexes[0].get("name") == "partition"
                and _iceberg_meta.issubset(set(indexes[0].get("column_names") or []))
            ):
                return []
            return indexes
        except NoSuchTableError:
            return []"""


def main() -> int:
    if not TRINO_PY.is_file():
        print(f"ERROR: {TRINO_PY} not found", file=sys.stderr)
        return 1
    text = TRINO_PY.read_text(encoding="utf-8")
    if NEW in text:
        print("patch already applied")
        return 0
    if OLD not in text:
        print("ERROR: patch anchor not found in trino.py (Superset version mismatch?)", file=sys.stderr)
        return 1
    TRINO_PY.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"patched {TRINO_PY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
