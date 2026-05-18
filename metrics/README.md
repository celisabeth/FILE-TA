# Folder Metrik Eksperimen

Hasil eksperimen ditulis ke `./metrics` (di Airflow: `/opt/airflow/metrics`).

## Skema audit (metadata / AQE / MLOps terpisah)

Setiap trigger DAG **metadata**, **AQE**, atau **MLOps** membuat **run folder baru** — run sebelumnya **tidak ditimpa**.

```
metrics/
  index.json                          # daftar semua run + pointer latest per track
  latest/
    metadata/experiment_summary.json  # run metadata terakhir saja
    aqe/aqe_comparison.json
    mlops/mlops_metrics.json
  runs/
    metadata_20260518T120114Z_a1b2c3/
      manifest.json
      staging_to_bronze_*.json
      silver_to_gold_*.json
      experiment_summary_*.json
      metadata_quality_*.json
      ...
    aqe_20260518T140000Z_d4e5f6/
      bronze_to_silver_aqe_OFF_*.json
      bronze_to_silver_aqe_ON_*.json
      aqe_comparison_*.json
    mlops_20260518T150000Z_g7h8i9/
      mlops_metrics_*.json
```

| Pertanyaan | Jawaban |
|------------|---------|
| Run ulang metadata, lalu AQE, lalu MLOps? | **Ya**, masing-masing folder `runs/{run_id}/` baru |
| Apakah data lama hilang? | **Tidak** — file ber-timestamp tetap di folder run lama |
| Apa yang di-update? | Hanya `latest/{track}/` dan entri `latest` di `index.json` untuk track itu |
| `experiment_summary_latest.json` di root? | **Legacy** — gunakan `latest/metadata/experiment_summary.json` |

## Lihat daftar run

```bash
python3 scripts/benchmark/list_experiment_runs.py
python3 scripts/benchmark/list_experiment_runs.py --track aqe
python3 scripts/benchmark/list_experiment_runs.py --json
```

## Label run (opsional)

Saat trigger DAG, kirim conf JSON:

```bash
docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment \
  --conf '{"label":"bab4-run1","notes":"setelah generate_data full"}'
```

## Izin folder

```bash
mkdir -p metrics && chmod 1777 metrics
docker compose run --rm metrics-init
```

## Menjalankan

```bash
docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment
docker exec lhmeta-airflow-scheduler airflow dags trigger aqe_full_experiment
docker exec lhmeta-airflow-scheduler airflow dags trigger mlops_pipeline
```

Panduan lengkap: [`../docs/eksperimen/README.md`](../docs/eksperimen/README.md)
