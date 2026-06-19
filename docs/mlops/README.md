# Pipeline MLOps — Forecast · Risk · Opportunity · Anomalies

Acuan diagram: [`../../MLOps-pipeline.png`](../../MLOps-pipeline.png)

| Komponen | Lokasi |
|----------|--------|
| DAG | `scripts/dags/mlops_pipeline.py` |
| Modul | `scripts/mlops/` |
| Registry | MLflow — http://localhost:15500 |
| Metrik Grafana | [`../monitoring-grafana/README.md`](../monitoring-grafana/README.md) |
| **Panduan model, metrik, inference, Superset** | **[`panduan-model-metrik-dan-superset.md`](panduan-model-metrik-dan-superset.md)** |
| SQL Superset | [`../gold-to-serving/templates/08-mlops-superset-sql.md`](../gold-to-serving/templates/08-mlops-superset-sql.md) |

---

## Empat use case

| # | Use case | Tipe ML | Model disarankan | Metrik utama |
|---|----------|---------|------------------|--------------|
| 1 | **Forecast** | Deret waktu / regresi | statsmodels ETS, sklearn Ridge, Spark `GBTRegressor` | MAE, RMSE, MAPE |
| 2 | **Risk Score** | Klasifikasi | sklearn / Spark `RandomForest`, `GBTClassifier` | Accuracy, F1, ROC-AUC |
| 3 | **Opportunity** | Clustering | Spark / sklearn `KMeans` | Silhouette |
| 4 | **Anomalies** | Unsupervised | `IsolationForest`, PyOD LOF | Anomaly rate, Precision@k |

Detail fitur Gold, alur inference data baru, dan dashboard Superset: lihat **[panduan lengkap](panduan-model-metrik-dan-superset.md)**.

---

## Alur DAG

```
init_experiment_run
  → data_preprocessing      (baca fact_* Gold)
  → feature_engineering     (s3a://mlops/features/iku_features)
  → train_models            (MLflow: risk_score_prodi + placeholder lain)
  → inference_batch         (fact_risk_score_mlops, fact_forecast_iku_mlops, …)
  → export_mlops_metrics    (metrics/runs/mlops_*/ → Grafana)
```

```bash
# Setelah metadata_full_experiment sukses
docker exec lhmeta-airflow-scheduler airflow dags trigger mlops_pipeline
```

---

## Modul

| File | Fungsi |
|------|--------|
| [`data_preprocessing.py`](../../scripts/mlops/data_preprocessing.py) | Validasi tabel Gold masukan |
| [`feature_engineering.py`](../../scripts/mlops/feature_engineering.py) | Fitur dari `fact_rekap_iku_institusi` × `dim_waktu` |
| [`train_models.py`](../../scripts/mlops/train_models.py) | Latih + log MLflow (Risk aktif; lainnya placeholder) |
| [`inference_batch.py`](../../scripts/mlops/inference_batch.py) | Tulis tabel `fact_*_mlops` + payload Grafana |

---

## Output Gold (serving)

| Tabel | Use case |
|-------|----------|
| `lakehouse.gold.fact_forecast_iku_mlops` | Forecast |
| `lakehouse.gold.fact_risk_score_mlops` | Risk Score |
| `lakehouse.gold.fact_opportunity_mlops` | Opportunity *(rencana)* |
| `lakehouse.gold.fact_anomaly_mlops` | Anomalies *(rencana)* |

Query Superset: template [08-mlops-superset-sql.md](../gold-to-serving/templates/08-mlops-superset-sql.md).

---

## Status implementasi

| Model | Training | Inference dari MLflow | Superset dataset |
|-------|----------|----------------------|------------------|
| Risk Score | ✅ sklearn RF | ⚠️ scaffold hardcode | ✅ template 08 |
| Forecast | ⚠️ naive trend | ⚠️ dari rekap Gold | ✅ template 08 |
| Opportunity | ❌ placeholder | ❌ hardcode JSON | 📋 template siap |
| Anomaly | ❌ placeholder | ❌ hardcode JSON | 📋 template siap |

Legenda: ✅ ada · ⚠️ sebagian · ❌ belum · 📋 panduan siap

---

## Dokumen terkait

- [`../eksperimen/templates/10-metrik-mlops.md`](../eksperimen/templates/10-metrik-mlops.md) — isian BAB IV
- [`../gold-to-serving/templates/05-dashboard-mlops-prediktif.md`](../gold-to-serving/templates/05-dashboard-mlops-prediktif.md) — Grafana + Superset
- [`../gold-to-serving/README.md`](../gold-to-serving/README.md) — star schema IKU deskriptif
