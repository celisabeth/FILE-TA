# Template — Lingkungan Eksperimen (Insight)

> Salin ke laporan atau `experiment-runs/run-YYYY-MM-DD/`

## Identitas run

| Field | Nilai |
|-------|-------|
| ID eksperimen | INSIGHT-EXP-001 |
| Skenario | Insight-OFF / Insight-ON |
| Tanggal | |
| Repositori | Data-Lakehouse-Insight |
| Commit / tag | |

## Infrastruktur host

| Komponen | Spesifikasi |
|----------|-------------|
| OS | |
| CPU | |
| RAM | |
| Disk kosong | |
| Docker | |

## Stack Insight (tiga metode)

| Layanan | Versi / URL | Metode |
|---------|-------------|--------|
| Spark | 3.5.1 — http://localhost:18080 | Metadata, AQE, MLOps |
| Iceberg | 1.5.2 | Metadata |
| Atlas | 2.3.0 — http://localhost:22100 | Metadata, MLOps |
| Airflow | 2.9.1 — http://localhost:18681 | Semua |
| insightera Portal | http://localhost:13000 | Katalog + dashboard embed |
| Trino | http://localhost:18088 | AQE |
| Superset | http://localhost:18089 | AQE / Dashboard Insight |
| Grafana | http://localhost:13001 | AQE |
| MLflow | http://localhost:15500 | MLOps |
| `spark.sql.adaptive.enabled` (default) | false (override OFF/ON di DAG) | AQE |

## Konfigurasi AQE

### OFF

| Parameter | Nilai |
|-----------|-------|
| `spark.sql.adaptive.enabled` | false |
| `SPARK_AQE_SCENARIO` | OFF |

### ON

| Parameter | Nilai |
|-----------|-------|
| `spark.sql.adaptive.enabled` | true |
| `spark.sql.adaptive.coalescePartitions.enabled` | true |
| `spark.sql.adaptive.skewJoin.enabled` | true |
| `SPARK_AQE_SCENARIO` | ON |

## Catatan

-
