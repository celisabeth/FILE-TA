# Template 05 — Dashboard Prediktif (MLOps)

Melengkapi dashboard **deskriptif** Superset (IKU dari star schema — template [01](01-dashboard-executive-iku.md)) dengan empat use case **prediktif**.

| Lapisan | Alat | Panduan |
|---------|------|---------|
| **SQL / chart bisnis** | **Apache Superset** | [`08-mlops-superset-sql.md`](08-mlops-superset-sql.md) · [`../../mlops/panduan-model-metrik-dan-superset.md`](../../mlops/panduan-model-metrik-dan-superset.md) §7 |
| **Monitoring pipeline & snapshot** | Grafana Dashboard Insight | [`../../monitoring-grafana/README.md`](../../monitoring-grafana/README.md) |
| **Registry model** | MLflow | http://localhost:15500 · [`../../mlops/README.md`](../../mlops/README.md) |

---

## A. Prasyarat

1. `metadata_full_experiment` sukses (Gold terisi, `dim_prodi` ≈ 42 baris).
2. `mlops_pipeline` sukses:

```bash
docker exec lhmeta-airflow-scheduler airflow dags trigger mlops_pipeline
```

3. Trino:

```sql
SELECT COUNT(*) FROM lakehouse.gold.fact_risk_score_mlops;
SELECT COUNT(*) FROM lakehouse.gold.fact_forecast_iku_mlops;
```

---

## B. Rekomendasi model (ringkas)

| Use case | Model utama | Metrik evaluasi |
|----------|-------------|-----------------|
| **Forecast** | statsmodels ETS / sklearn Ridge | MAE, RMSE, MAPE |
| **Risk Score** | Random Forest / GBT (sklearn atau Spark MLlib) | Accuracy, F1, ROC-AUC |
| **Opportunity** | K-Means (k≈4) | Silhouette |
| **Anomalies** | Isolation Forest | Anomaly rate %, Precision@k |

Detail: [`../../mlops/panduan-model-metrik-dan-superset.md`](../../mlops/panduan-model-metrik-dan-superset.md).

---

## C. Superset — dashboard “Insight Prediktif”

Ikuti [`08-mlops-superset-sql.md`](08-mlops-superset-sql.md):

| Panel | Dataset | Chart |
|-------|---------|-------|
| Forecast | `v_forecast_iku_mlops` | Line — X: `tahun`, Y: `nilai_capaian`, series: `series_type` |
| Risk | `v_risk_score_prodi` | Bar horizontal — X: `nama_prodi`, Y: `risk_score` |
| Opportunity | `v_opportunity_prodi` | Bar — X: `nama_prodi`, Y: `opportunity_score` |
| Anomalies | `v_anomaly_iku` | Table / bar count |

Filter dashboard: `tahun`, `fakultas_id`.

---

## D. Grafana — panel monitoring (bukan pengganti Superset)

| Use case | Metrik Prometheus | Panel |
|----------|---------------------|-------|
| Forecast | `lakehouse_insight_forecast` | Actual vs forecast |
| Risk Score | `lakehouse_insight_risk_score` | Bar gauge per prodi |
| Opportunity | `lakehouse_insight_opportunity_score` | Bar |
| Anomalies | `lakehouse_insight_anomaly_count`, `_rate_percent` | Stat |

Diisi dari `export_mlops_metrics` setelah `inference_batch`.

---

## E. Kaitan Gold

| Output prediktif | Tabel Gold | Granularitas |
|------------------|------------|--------------|
| Risk Score | `fact_risk_score_mlops` | prodi × tahun |
| Forecast | `fact_forecast_iku_mlops` | tahun (agregat institusi) |
| Opportunity | `fact_opportunity_mlops` | prodi |
| Anomaly | `fact_anomaly_mlops` | prodi / IKU / tahun |

Fitur latih: `fact_rekap_iku_institusi`, `fact_iku*`, `dim_prodi`, `dim_waktu` — lihat panduan MLOps §2.

---

## F. Inference data baru

Setiap data staging/Gold diperbarui:

1. Trigger `metadata_full_experiment` (atau `silver_gold_pipeline`).
2. Trigger `mlops_pipeline` → `inference_batch` menulis ulang `fact_*_mlops`.
3. Refresh dataset Superset (atau auto-refresh cache).
4. Grafana memuat `metrics/latest/mlops/mlops_metrics.json`.

---

## G. Screenshot & catatan BAB IV

| File | Isi |
|------|-----|
| superset-mlops-forecast.png | Line forecast Superset |
| superset-mlops-risk.png | Risk per prodi |
| grafana-dashboard-insight.png | Snapshot monitoring |
| mlflow-risk-metrics.png | Accuracy / F1 di MLflow |

Isian metrik: [`../../eksperimen/templates/10-metrik-mlops.md`](../../eksperimen/templates/10-metrik-mlops.md).

---

## H. Catatan pembahasan

-
