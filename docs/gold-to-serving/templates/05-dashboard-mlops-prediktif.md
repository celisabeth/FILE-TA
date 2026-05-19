# Template 05 — Dashboard Prediktif (MLOps / Grafana)

> **Bukan Superset** — tidak ada langkah Dataset/Chart di sini.  
> KPI deskriptif (IKU) → template [01](01-dashboard-executive-iku.md) + [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md).

Melengkapi dashboard **deskriptif** Superset (Gold OLAP) dengan layer **prediktif** dari pipeline MLOps.

| Alat | URL | Panduan |
|------|-----|---------|
| Grafana Dashboard Insight | http://localhost:13001 | [`../../monitoring-grafana/README.md`](../../monitoring-grafana/README.md) |
| MLflow | http://localhost:15500 | [`../../mlops/README.md`](../../mlops/README.md) |

## Panel prediktif (isi dari Grafana)

| Use case | Metrik / panel | Nilai observasi | Interpretasi |
|----------|----------------|-----------------|--------------|
| Forecast | Actual vs forecast IKU | | |
| Risk Score | Skor per prodi | | |
| Opportunity | Indeks peluang | | |
| Anomalies | Count / rate % | | |

## Kaitan dengan Gold (star schema)

| Output prediktif | Tabel Gold / sumber | Granularitas |
|------------------|---------------------|--------------|
| Risk Score | `fact_risk_score_mlops` (scaffold) | Prodi |
| Forecast IKU | `fact_forecast_iku_mlops` | Tahun × IKU |
| Feature join | `dim_waktu`, `dim_prodi`, facts IKU | Sesuai training |

## Screenshot

| File |
|------|
| grafana-dashboard-insight.png |
| grafana-mlops-pipeline.png |

## Catatan pembahasan (BAB IV)

-
