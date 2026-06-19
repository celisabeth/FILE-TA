FROM apache/superset:4.0.2

# Trino: paket `trino` (bukan sqlalchemy-trino — max v0.5.0).
# Jangan upgrade pip/setuptools di image base: Superset 4.0.2 masih butuh pkg_resources (setuptools<81).
USER root
RUN pip install --no-cache-dir \
    "trino>=0.328,<0.340" \
    "setuptools>=65.0.0,<81.0.0"

# Iceberg + Trino: jangan treat record_count/file_count sebagai kolom partisi (Superset #26449)
COPY patch_trino_iceberg.py /tmp/patch_trino_iceberg.py
RUN python3 /tmp/patch_trino_iceberg.py && rm /tmp/patch_trino_iceberg.py

USER superset

COPY superset_config.py /app/pythonpath/superset_config.py
# Gagalkan build jika config lama (import Trino saat load) ikut ter-copy
RUN ! grep -q '_patch_trino_iceberg_partition_indexes' /app/pythonpath/superset_config.py \
    && grep -q '_iceberg_meta' /app/superset/db_engine_specs/trino.py
ENV SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py
