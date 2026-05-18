# Benchmark & Metrik — Data Lakehouse Insight

Skrip pengukuran untuk **tiga metode**: Metadata, AQE, MLOps. Output ke `metrics/` (volume Docker `/opt/airflow/metrics`).

## Skrip per metode

| Skrip | Metode | Output |
|-------|--------|--------|
| `dataset_summary.py` | Umum | `dataset_summary_*.json` |
| `atlas_quality.py` | Metadata | `metadata_quality_*.json` |
| `atlas_inventory.py` | Metadata | `atlas_inventory_*.json` |
| `collect_umt.py` | Metadata | `umt_*.json` |
| `aggregate_results.py` | Gabungan | `experiment_summary_*.json` |
| `compare_aqe_runs.py` | AQE | `aqe_comparison_*.json` |
| `run_spark_workloads.py` | AQE | `workloads_spark_aqe_{OFF\|ON}_*.json` |
| `run_trino_workloads.py` | AQE | `workloads_trino_ctx_{OFF\|ON}_*.json` |
| `metrics_exporter.py` | AQE | HTTP `/metrics` → Prometheus/Grafana |
| `run_experiment.py` | Metadata | Orkestrator metadata saja |

Pipeline Spark menulis otomatis: `staging_to_bronze_*.json`, `bronze_to_silver_*.json`, `bronze_to_silver_aqe_{OFF\|ON}_*.json`, `silver_to_gold_*.json`.

## Jalankan eksperimen penuh (Insight)

```bash
export INSIGHT_METRICS_DIR=metrics   # atau META_METRICS_DIR / AQE_METRICS_DIR
mkdir -p metrics && chmod 1777 metrics

# Urutan DAG (lihat docs/eksperimen/README.md)
docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment
docker exec lhmeta-airflow-scheduler airflow dags trigger aqe_full_experiment
docker exec lhmeta-airflow-scheduler airflow dags trigger mlops_pipeline

# Agregasi & perbandingan AQE
PYTHONPATH=scripts INSIGHT_METRICS_DIR=metrics python3 scripts/benchmark/compare_aqe_runs.py --markdown
PYTHONPATH=scripts INSIGHT_METRICS_DIR=metrics python3 scripts/benchmark/aggregate_results.py --write-latest
```

## Grafana

http://localhost:13001 — dashboard **Lakehouse AQE Experiment** (setelah `aqe_full_experiment`).

## Pemetaan BAB IV

| Output | Subbab |
|--------|--------|
| `metadata_quality_*.json` | §4.1.6 |
| `aqe_comparison_*.json` | §4.1.2–4.1.4 |
| `umt_*.json` | §4.1.4 |
| `experiment_summary_latest.json` | Ringkasan |

Panduan: [`../../docs/eksperimen/README.md`](../../docs/eksperimen/README.md)
