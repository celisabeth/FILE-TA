#!/usr/bin/env bash
# One-shot Airflow DB migrate + admin user (Airflow 2.9.x)
set -euo pipefail

echo "=== Airflow init: ensure PostgreSQL databases ==="
python3 <<'PY'
import os
import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

host = os.environ.get("PGHOST", "postgres")
user = os.environ.get("PGUSER", "admin")
password = os.environ.get("PGPASSWORD", "admin123")
dbs = ("airflow_db", "iceberg_catalog", "superset_db", "mlflow_db")

conn = psycopg2.connect(host=host, user=user, password=password, dbname="postgres")
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
for name in dbs:
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
    if cur.fetchone():
        print(f"  database exists: {name}")
    else:
        cur.execute(f'CREATE DATABASE "{name}"')
        print(f"  created database: {name}")
cur.close()
conn.close()
PY

mkdir -p /opt/airflow/metrics
chmod 1777 /opt/airflow/metrics 2>/dev/null || true

echo "=== Airflow init: db migrate (schema) ==="
airflow db migrate

echo "=== Airflow init: admin user ==="
airflow users create \
  --username airflow \
  --password airflow \
  --firstname Air \
  --lastname Flow \
  --role Admin \
  --email airflow@lakehouse.local 2>/dev/null \
  || echo "  (admin user already exists — OK)"

echo "=== Airflow init: done ==="
