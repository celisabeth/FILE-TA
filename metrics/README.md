# Folder Metrik Eksperimen

Hasil eksperimen metadata otomatis ditulis ke folder ini (di VM/host: `./metrics`, di container Airflow: `/opt/airflow/metrics`).

## File utama

| File | Isi |
|------|-----|
| `experiment_summary_latest.json` | Ringkasan seluruh run |
| `dataset_summary_*.json` | Statistik CSV staging |
| `staging_to_bronze_*.json` | Runtime pipeline + profiling Bronze |
| `bronze_to_silver_*.json` | Runtime pipeline Silver |
| `silver_to_gold_*.json` | Runtime pipeline Gold (star schema) |
| `atlas_registration_{layer}_*.json` | Jumlah entitas Atlas per layer |
| `metadata_quality_latest.json` | Completeness / accuracy / timeliness / consistency |
| `atlas_inventory_latest.json` | Coverage + lineage completeness |
| `umt_latest.json` | Unified Metadata Table snapshot |

## Menjalankan

```bash
docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment
```

Panduan lengkap: [`../docs/eksperimen/README.md`](../docs/eksperimen/README.md)
