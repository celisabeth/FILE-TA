import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "lakehouse_superset_secret_change_me")
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://admin:admin123@postgres:5432/superset_db",
)
WTF_CSRF_ENABLED = True
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}


def _patch_trino_iceberg_partition_indexes() -> None:
    """
    Superset + Trino + Iceberg: get_indexes() mengembalikan pseudo-partisi
    (record_count, file_count, total_size, data) yang ikut disisipkan ke SQL Lab
    → Trino: Column 'record_count' cannot be resolved.
    Ref: https://github.com/apache/superset/issues/26449
    """
    try:
        from superset.db_engine_specs.trino import TrinoEngineSpec
    except ImportError:
        return

    _original = TrinoEngineSpec.get_indexes.__func__  # type: ignore[attr-defined]

    @classmethod
    def get_indexes(cls, database, inspector, table_name, schema):  # noqa: ANN001
        try:
            indexes = _original(cls, database, inspector, table_name, schema)
        except Exception:
            return []
        iceberg_meta = {"record_count", "file_count", "total_size", "data"}
        if (
            len(indexes) == 1
            and indexes[0].get("name") == "partition"
            and iceberg_meta.issubset(set(indexes[0].get("column_names") or []))
        ):
            return []
        return indexes

    TrinoEngineSpec.get_indexes = get_indexes  # type: ignore[method-assign]


_patch_trino_iceberg_partition_indexes()
