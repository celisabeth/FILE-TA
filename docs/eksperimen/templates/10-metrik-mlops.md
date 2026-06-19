# Template — Metrik MLOps (BAB IV §4.1.4)

Sumber: MLflow http://localhost:15500, log DAG `mlops_pipeline`, tabel output Gold.

## Identitas run MLOps

| Item | Nilai |
|------|-------|
| DAG | `mlops_pipeline` |
| Tanggal | |
| Gold source | `metadata_full_experiment` selesai |

## Model registry (GM: Gold-MLOps)

| Model | Versi | Status | Run ID | Metrik utama |
|-------|-------|--------|--------|--------------|
| risk_score_prodi | | Staging/Production | | accuracy / F1 |
| forecast_iku | | | | MAE / RMSE |
| opportunity_prodi | | | | |
| anomaly_detector_iku | | | | |

## Output tables

| Tabel | Baris | Path / schema | Terdaftar Atlas |
|-------|-------|---------------|-----------------|
| fact_risk_score_mlops | | lakehouse.gold.* | ya/tidak |
| fact_forecast_iku | | | |
| fact_opportunity | | | |
| fact_anomaly | | | |

## Durasi pipeline MLOps

| Task | Durasi (s) | Status |
|------|------------|--------|
| data_preprocessing | | |
| feature_engineering | | |
| train_models | | |
| inference_batch | | |
| export_mlops_metrics | | |
| **Total** | | |

## Grafana — Dashboard Insight

Sumber metrik: `metrics/mlops_metrics_latest.json` → Prometheus (`lakehouse_insight_*`, `lakehouse_mlops_*`).

Panduan: [`../../monitoring-grafana/README.md`](../../monitoring-grafana/README.md)

| Panel | Metrik Prometheus | Nilai contoh (isi dari Grafana) |
|-------|-------------------|--------------------------------|
| Forecast actual vs prediksi | `lakehouse_insight_forecast` | |
| Risk Score per prodi | `lakehouse_insight_risk_score` | |
| Opportunity per prodi | `lakehouse_insight_opportunity_score` | |
| Anomalies count / rate | `lakehouse_insight_anomaly_count`, `lakehouse_insight_anomaly_rate_percent` | |
| MLOps task duration | `lakehouse_mlops_task_duration_seconds` | |

## Metadata MLOps di Atlas (AI Metadata)

| Atribut | Contoh nilai | Terisi |
|---------|--------------|--------|
| qualifiedName model | mlops.risk_score_prodi@lakehouse | |
| training_data lineage | silver.* → model | |
| deployment_status | Production | |

## Screenshot

| No | File |
|----|------|
| 1 | mlflow-experiments.png |
| 2 | mlflow-registry.png |
| 3 | grafana-dashboard-insight.png |
| 4 | grafana-mlops-pipeline.png |

## Catatan pembahasan

-
