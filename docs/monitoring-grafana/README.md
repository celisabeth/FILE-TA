# Monitoring Grafana — Dashboard Insight & MLOps Pipeline

Panduan observabilitas untuk **empat use case prediktif** (Forecast, Risk Score, Opportunity, Anomalies) dan **monitoring pipeline MLOps**, selaras dengan diagram [`MLOps-pipeline.png`](../../MLOps-pipeline.png) dan fase eksperimen di [`../eksperimen/README.md`](../eksperimen/README.md).

**Prasyarat:** stack berjalan (`./start.sh`), folder `metrics/` ada dan dapat ditulis.

| Service | URL | Login |
|---------|-----|-------|
| **Grafana** | http://localhost:13001 | admin / admin |
| **Prometheus** | http://localhost:19090 | — |
| **Metrics exporter** | http://localhost:9101/metrics | — |
| **MLflow** | http://localhost:15500 | — |
| **Airflow** | http://localhost:18681 | airflow / airflow |

---

## 1. Dashboard yang tersedia

Provisioning otomatis dari [`../../monitoring/grafana/provisioning/`](../../monitoring/grafana/provisioning/). Setelah Grafana start, buka **Dashboards → folder Lakehouse Insight**.

| Dashboard | UID | Isi panel |
|-----------|-----|-----------|
| **Dashboard Insight — Forecast · Risk · Opportunity · Anomalies** | `lakehouse-dashboard-insight` | Time series actual vs forecast; bar gauge Risk Score & Opportunity; stat + time series Anomalies |
| **MLOps Pipeline Monitoring** | `lakehouse-mlops-pipeline` | Durasi task DAG; metrik training MLflow; ringkasan output use case |
| **Lakehouse AQE Experiment** | `lakehouse-aqe-experiment` | Speedup Silver, durasi pipeline & workload (metode AQE) |

File JSON sumber:

- [`../../monitoring/grafana/provisioning/dashboards/json/dashboard-insight.json`](../../monitoring/grafana/provisioning/dashboards/json/dashboard-insight.json)
- [`../../monitoring/grafana/provisioning/dashboards/json/mlops-pipeline.json`](../../monitoring/grafana/provisioning/dashboards/json/mlops-pipeline.json)
- [`../../monitoring/grafana/provisioning/dashboards/json/aqe-experiment.json`](../../monitoring/grafana/provisioning/dashboards/json/aqe-experiment.json)

---

## 2. Arsitektur alur metrik

```
┌─────────────────────────────────────────────────────────────────┐
│  DAG mlops_pipeline (Airflow)                                   │
│  preprocessing → features → train_models → inference_batch      │
│                              → export_mlops_metrics             │
└────────────────────────────┬────────────────────────────────────┘
                             │ metrics/mlops_metrics_latest.json
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  metrics-exporter (:9101)  — scripts/benchmark/metrics_exporter │
│  Membaca juga: aqe_comparison_*, bronze_to_silver_aqe_*, dll.   │
└────────────────────────────┬────────────────────────────────────┘
                             │ scrape 15s
                             ▼
                    ┌─────────────────┐
                    │   Prometheus    │  :19090
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    Grafana      │  :13001
                    └─────────────────┘
```

---

## 3. Metrik Prometheus (Dashboard Insight)

Diekspor dari `mlops_metrics_latest.json` oleh [`../../scripts/benchmark/metrics_exporter.py`](../../scripts/benchmark/metrics_exporter.py).

| Metrik | Label | Use case |
|--------|-------|----------|
| `lakehouse_insight_forecast` | `series`, `tahun`, `iku_code` | Forecast — actual vs prediksi capaian IKU |
| `lakehouse_insight_risk_score` | `prodi_id`, `nama_prodi` | Risk Score per program studi (0–100) |
| `lakehouse_insight_opportunity_score` | `prodi_id`, `cluster` | Opportunity / peluang peningkatan |
| `lakehouse_insight_anomaly_count` | — | Jumlah record ter-flag anomali |
| `lakehouse_insight_anomaly_rate_percent` | — | Persentase anomali |
| `lakehouse_insight_anomaly_flag` | `entity`, `tahun`, `metric` | Sampel nilai ter-flag |

### Metrik MLOps pipeline

| Metrik | Label | Keterangan |
|--------|-------|------------|
| `lakehouse_mlops_task_duration_seconds` | `task` | Durasi task DAG (dari Airflow) |
| `lakehouse_mlops_model_metric` | `model`, `metric` | Accuracy, MAE, dll. dari training |

Contoh query di Prometheus:

```promql
lakehouse_insight_risk_score
lakehouse_mlops_task_duration_seconds{task="inference_batch"}
```

---

## 4. Cara mengisi dashboard (langkah demi langkah)

### 4.1 Demo cepat (tanpa menunggu pipeline penuh)

```bash
cd Data-Lakehouse-Insight
mkdir -p metrics && chmod 1777 metrics

PYTHONPATH=scripts INSIGHT_METRICS_DIR=metrics \
  python3 scripts/benchmark/mlops_metrics.py --demo
```

Tunggu ±15 detik (interval scrape Prometheus), lalu buka Grafana → **Dashboard Insight**.

Payload demo didefinisikan di [`../../scripts/benchmark/mlops_metrics.py`](../../scripts/benchmark/mlops_metrics.py) (`_demo_insight_payload`) agar panel tidak kosong sebelum model production siap.

### 4.2 Setelah DAG MLOps sukses

```bash
docker exec lhmeta-airflow-scheduler airflow dags trigger mlops_pipeline
```

Task terakhir `export_mlops_metrics` menulis `metrics/mlops_metrics_latest.json` dengan hasil inference aktual (risk, forecast, opportunity, anomaly) bila tersedia dari [`../../scripts/mlops/inference_batch.py`](../../scripts/mlops/inference_batch.py).

Verifikasi file:

```bash
cat metrics/mlops_metrics_latest.json | python3 -m json.tool | head -40
curl -s http://localhost:9101/metrics | grep lakehouse_insight
```

### 4.3 Reload dashboard

- Grafana auto-provision saat container start.
- Jika mengubah JSON dashboard: `docker compose restart grafana`
- Refresh panel: tombol refresh (default 30s) atau time range **Last 6 hours**

---

## 5. Pemetaan panel per use case

### 5.1 Forecast

- **Panel:** *Forecast — Capaian IKU (Actual vs Prediksi)*
- **Sumber data:** `dashboard_insight.forecast.series` di JSON → `lakehouse_insight_forecast{series="actual|forecast"}`
- **Tabel Gold (target):** `lakehouse.gold.fact_forecast_iku_mlops`

### 5.2 Risk Score

- **Panel:** *Risk Score — per Prodi* (bar gauge, threshold merah &lt; 60, hijau ≥ 80)
- **Metrik:** `lakehouse_insight_risk_score`
- **Bukan error:** warna merah/kuning = skor rendah menurut threshold, bukan kegagalan scrape. Panel memakai query `instant` (snapshot terakhir).
- **Tabel Gold:** `lakehouse.gold.fact_risk_score_mlops`

### 5.3 Opportunity

- **Panel:** *Opportunity — Skor Peluang per Prodi*
- **Metrik:** `lakehouse_insight_opportunity_score` (label `cluster`)

### 5.4 Anomalies

- **Panel:** jumlah flag, rate %, bar chart sampel ter-flag
- **Metrik:** `lakehouse_insight_anomaly_count`, `lakehouse_insight_anomaly_rate_percent`, `lakehouse_insight_anomaly_flag`
- **Catatan:** label `tahun` di Prometheus bukan sumbu waktu — jangan pakai panel *Time series* (titik hanya muncul di kanan). Dashboard v2 memakai *Bar chart* + `instant: true`.

### 5.5 MLOps pipeline

Dashboard **MLOps Pipeline Monitoring** menampilkan:

1. Durasi per task (`data_preprocessing`, `feature_engineering`, `train_models`, `inference_batch`)
2. Metrik model dari MLflow (via blok `training.models` di JSON)
3. Stat ringkasan jumlah series risk / forecast / opportunity / anomaly

---

## 6. Integrasi dengan eksperimen penelitian

| Fase | DAG | Dashboard terkait |
|------|-----|-------------------|
| B — AQE | `aqe_full_experiment` | Lakehouse AQE Experiment |
| C — MLOps | `mlops_pipeline` | Dashboard Insight + MLOps Pipeline |

Template laporan:

- [`../eksperimen/templates/09-perbandingan-aqe.md`](../eksperimen/templates/09-perbandingan-aqe.md) — screenshot Grafana AQE
- [`../eksperimen/templates/10-metrik-mlops.md`](../eksperimen/templates/10-metrik-mlops.md) — tambahkan screenshot panel Forecast / Risk / Opportunity / Anomalies

**Screenshot disarankan** (simpan di `docs/screenshots/`):

- `grafana-dashboard-insight.png`
- `grafana-mlops-pipeline.png`
- `grafana-aqe-experiment.png`

---

## 7. Troubleshooting

| Gejala | Penyebab umum | Solusi |
|--------|---------------|--------|
| Panel *No data* | `mlops_metrics_latest.json` belum ada | Jalankan §4.1 atau trigger `mlops_pipeline` |
| Metrik tidak muncul di Prometheus | Exporter / scrape mati | `curl http://localhost:9101/metrics`; cek target di http://localhost:19090/targets |
| Prometheus: `lookup metrics-exporter ... server misbehaving` | Container exporter crash (mis. `ModuleNotFoundError: benchmark`) | `docker compose logs metrics-exporter`; pastikan `PYTHONPATH=/app/scripts`; `docker compose up -d metrics-exporter prometheus` |
| Panel workload Trino kosong / tidak ada `workloads_trino_*.json` | Task Trino belum dijalankan atau Gold AQE belum ada | Jalankan DAG `aqe_full_experiment` sampai `trino_workloads_off/on` sukses; atau manual §7.1 |
| Forecast/Anomali hanya garis titik di kanan; Risk “merah” | Metrik insight = snapshot (bukan deret waktu); threshold Risk | Pull dashboard v2; `docker compose restart grafana`; Forecast/Anomali pakai bar chart |
| Workload AQE hanya titik di kanan chart | Panel time series untuk metrik snapshot scrape | Dashboard `lakehouse-aqe-experiment` v2: workload → bar chart + `instant: true` |
| MLOps: time series task kosong; Model Training *No data* | Duplikat panel time series; `training.models` tanpa angka | Dashboard `lakehouse-mlops-pipeline` v2; jalankan `mlops_pipeline` atau `mlops_metrics.py --demo` lalu restart exporter |
| Dashboard tidak muncul | Path provisioning salah | Pastikan volume `./monitoring/grafana/provisioning` di `docker-compose.yml` |
| Nilai masih demo | Inference belum mengisi payload | Cek return `inference_batch` dan field `risk_score_rows`, `forecast_series`, dll. |
| Task duration 0 | DAG belum selesai / inst.duration null | Jalankan ulang DAG; duration terisi setelah task **success** |

### 7.1 Workload Trino (W4–W6) — generate JSON & Grafana

Prasyarat: Trino jalan, Gold AQE terisi (`silver_to_gold_off/on` sukses di DAG `aqe_full_experiment`).

```bash
# Cek tabel Gold AQE OFF
docker exec lhmeta-trino trino --execute "SHOW TABLES FROM lakehouse_aqe_off.gold_aqe_off"

# Jalankan workload Trino (OFF lalu ON)
docker exec lhmeta-airflow-scheduler python /opt/airflow/scripts/benchmark/run_trino_workloads.py --aqe-context OFF
docker exec lhmeta-airflow-scheduler python /opt/airflow/scripts/benchmark/run_trino_workloads.py --aqe-context ON

# Verifikasi artefak
ls -la metrics/workloads_trino_ctx_*.json metrics/latest/aqe/workloads_trino_ctx_*.json 2>/dev/null
curl -s http://localhost:9101/metrics | grep 'lakehouse_workload_duration_seconds.*trino'
```

Atau trigger DAG penuh:

```bash
docker exec lhmeta-airflow-scheduler airflow dags trigger aqe_full_experiment
```

Panel Grafana **Workload Duration — Spark & Trino** memakai `lakehouse_workload_duration_seconds{engine="trino"}`.

Restart stack monitoring:

```bash
docker compose restart metrics-exporter prometheus grafana
```

---

## 8. Referensi kode

| Komponen | Path |
|----------|------|
| Kumpulkan JSON MLOps | `scripts/benchmark/mlops_metrics.py` |
| Ekspor Prometheus | `scripts/benchmark/metrics_exporter.py` |
| DAG + task export | `scripts/dags/mlops_pipeline.py` |
| Inference → metrik insight | `scripts/mlops/inference_batch.py` |
| Provisioning Grafana | `monitoring/grafana/provisioning/` |
| Scrape config | `monitoring/prometheus/prometheus.yml` |

Panduan AQE terperinci (shuffle, partisi, resource): salinan konsep dari repo AQE — lihat juga [`../../../Data-Lakehouse-AQE/docs/monitoring-grafana/README.md`](../../../Data-Lakehouse-AQE/docs/monitoring-grafana/README.md) untuk metrik performa Spark/Trino.
