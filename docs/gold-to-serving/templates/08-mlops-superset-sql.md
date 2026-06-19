# Template 08 — Virtual Dataset Superset (MLOps / Insight Prediktif)

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)  
**Panduan model & metrik:** [`../../mlops/panduan-model-metrik-dan-superset.md`](../../mlops/panduan-model-metrik-dan-superset.md)

**Prasyarat:** DAG `mlops_pipeline` sukses · Trino: `SHOW TABLES FROM lakehouse.gold LIKE '%mlops%'`

---

## Diagnosa

```sql
SELECT COUNT(*) AS n_risk FROM lakehouse.gold.fact_risk_score_mlops;
```

```sql
SELECT COUNT(*) AS n_forecast FROM lakehouse.gold.fact_forecast_iku_mlops;
```

| Hasil | Tindakan |
|-------|----------|
| 0 | `airflow dags trigger mlops_pipeline` setelah Gold terisi |
| > 0 | Lanjut buat dataset di bawah |

---

## v_forecast_iku_mlops

```sql
SELECT tahun,
       nilai_capaian,
       CASE WHEN is_forecast = 1 THEN 'forecast' ELSE 'actual' END AS series_type
FROM lakehouse.gold.fact_forecast_iku_mlops
ORDER BY tahun;
```

| Chart | **X-Axis** | **Y-Axis (Metrics)** |
|-------|------------|----------------------|
| Line Chart | `tahun` | AVG `nilai_capaian` |
| Series / Breakdown | `series_type` | — |

**Metrik evaluasi (MLflow / laporan):** MAE, RMSE, MAPE — bandingkan baris `actual` vs `forecast` di tahun validasi.

---

## v_risk_score_prodi

```sql
SELECT r.tahun, r.prodi_id, p.nama_prodi, p.fakultas_id, p.nama_fakultas,
       r.risk_score, r.scored_at
FROM lakehouse.gold.fact_risk_score_mlops r
LEFT JOIN lakehouse.gold.dim_prodi p ON r.prodi_id = p.prodi_id
ORDER BY r.risk_score DESC;
```

| Chart | **X-Axis** | **Y-Axis** |
|-------|------------|------------|
| Bar horizontal | `nama_prodi` | AVG `risk_score` |
| Table | — | semua kolom |

**Filter:** `tahun` = `2024` · **Metrik klasifikasi:** Accuracy, F1, ROC-AUC (dari MLflow `risk_score_prodi`).

---

## v_forecast_vs_target (gabung deskriptif)

```sql
SELECT w.tahun, r.iku_kode, r.nilai_capaian AS actual, r.nilai_target AS target
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
WHERE r.iku_kode = 'IKU-4'
ORDER BY w.tahun;
```

Chart terpisah untuk baris `forecast` dari `v_forecast_iku_mlops` — bandingkan trend actual vs prediksi vs target Renstra.

---

## v_opportunity_prodi *(setelah `fact_opportunity_mlops` ada)*

```sql
SELECT o.prodi_id, p.nama_prodi, p.nama_fakultas,
       o.cluster, o.opportunity_score, o.scored_at
FROM lakehouse.gold.fact_opportunity_mlops o
JOIN lakehouse.gold.dim_prodi p ON o.prodi_id = p.prodi_id
ORDER BY o.opportunity_score DESC;
```

| Chart | **X-Axis** | **Y-Axis** |
|-------|------------|------------|
| Bar | `nama_prodi` | AVG `opportunity_score` |
| Pie / Bar | `cluster` | COUNT prodi |

**Metrik clustering:** Silhouette (MLflow).

---

## v_anomaly_iku *(setelah `fact_anomaly_mlops` ada)*

```sql
SELECT tahun, iku_code, prodi_id, metric_name, nilai,
       is_anomaly, anomaly_score
FROM lakehouse.gold.fact_anomaly_mlops
WHERE is_anomaly = 1
ORDER BY anomaly_score DESC;
```

| Chart | **X-Axis** | **Y-Axis** |
|-------|------------|------------|
| Bar | `iku_code` | COUNT `*` |
| Big Number | — | COUNT anomali |

**Metrik:** anomaly rate %, Precision@k (jika ada label audit).

---

## Dashboard “Insight Prediktif ITERA”

| Panel | Dataset |
|-------|---------|
| Forecast actual vs prediksi | `v_forecast_iku_mlops` |
| Risk per prodi | `v_risk_score_prodi` |
| Opportunity | `v_opportunity_prodi` |
| Anomali terdeteksi | `v_anomaly_iku` |
| Filter | `tahun`, `fakultas_id` |

**Grafana (monitoring):** tetap [`../../monitoring-grafana/README.md`](../../monitoring-grafana/README.md) — snapshot `lakehouse_insight_*`, bukan pengganti chart Superset di atas.

---

## Checklist screenshot

| File | Isi |
|------|-----|
| superset-mlops-forecast.png | Line forecast |
| superset-mlops-risk.png | Bar risk per prodi |
| superset-mlops-opportunity.png | Cluster / skor |
| superset-mlops-anomaly.png | Tabel anomali |
