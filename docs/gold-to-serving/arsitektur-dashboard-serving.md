# Arsitektur Dashboard Serving — Rekomendasi (Superset vs Grafana, AQE OFF/ON)

Dokumen ini menjawab: **apakah perlu 2 dashboard KPI di portal untuk `lakehouse_aqe_off` dan `lakehouse_aqe_on`?** **Apakah pengukuran lewat metrik Grafana?** **Apakah Superset hanya untuk katalog `lakehouse`?**

---

## 1. Jawaban singkat

| Pertanyaan | Jawaban |
|------------|---------|
| 2 dashboard KPI AQE OFF/ON di portal? | **Ya, opsional di Superset** — untuk membandingkan **nilai KPI bisnis** dari dua salinan Gold (audit data parity). Bukan duplikasi Monitoring Grafana. |
| Pengukuran performa AQE? | **Grafana + Prometheus + `metrics/`** — speedup Spark/Trino, durasi DAG, bukan chart IKU di Grafana. |
| Superset hanya `lakehouse`? | **Utama: `lakehouse.gold`**. Koneksi tambahan **`lakehouse_aqe_off`** / **`lakehouse_aqe_on`** hanya untuk eksperimen BAB IV. |

---

## 2. Tiga lapisan pengukuran

```
┌─────────────────────────────────────────────────────────────────┐
│  GOLD (Iceberg)                                                  │
│  • lakehouse.gold          ← jalur governance / operasional       │
│  • lakehouse.gold_aqe_off  ← salinan eksperimen AQE OFF          │
│  • lakehouse.gold_aqe_on   ← salinan eksperimen AQE ON           │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
                ▼                             ▼
     ┌──────────────────────┐    ┌──────────────────────────────┐
     │  SUPerset (OLAP KPI)  │    │  Grafana (metrik pipeline)    │
     │  • Nilai IKU, SAKIP   │    │  • Durasi task, speedup AQE   │
     │  • Roll-up prodi      │    │  • Forecast / Risk (MLOps)  │
     │  • SQL → Trino        │    │  • Prometheus lakehouse_*   │
     └──────────────────────┘    └──────────────────────────────┘
                │                             │
                ▼                             ▼
     Portal: /dashboards/analitik     Portal: /dashboards/monitoring-aqe
             /dashboards/kpi-aqe-off           /dashboards/insight
             /dashboards/kpi-aqe-on            /dashboards/monitoring-mlops
```

### 2.1 Superset — **apa yang diukur**

- **Metrik bisnis** dari tabel fakta: `nilai_capaian`, `persen_iku4`, `status_capaian`, dll.
- **Sumber:** SQL Trino ke star schema (`fact_*`, `dim_*`).
- **Katalog:**
  - **Wajib:** `lakehouse` → schema **`gold`** (Gold utama, tidak tertimpa eksperimen AQE).
  - **Opsional penelitian:** `lakehouse_aqe_off` / `lakehouse_aqe_on` → schema **`gold_aqe_off`** / **`gold_aqe_on`** — KPI **harusnya setara** jika pipeline benar; perbedaan kecil bisa muncul dari timing/materialisasi.

### 2.2 Grafana — **apa yang diukur**

- **Metrik teknis eksperimen:** `lakehouse_aqe_speedup_ratio`, durasi Silver/Gold, task Airflow, ekspor JSON di `metrics/aqe_comparison_*.json`.
- **MLOps prediktif:** Forecast, Risk, Opportunity, Anomalies (bukan pengganti Executive IKU Superset).
- **Satu** dashboard Grafana `lakehouse-aqe-experiment` sudah membandingkan **OFF vs ON** dalam satu layar — **tidak perlu** 2 halaman Grafana terpisah untuk OFF/ON.

### 2.3 Portal KPI (`/kpi`)

- Ringkasan metadata / Atlas-backed — melengkapi, bukan mengganti Superset chart.

---

## 3. Kapan memakai 2 dashboard Superset OFF/ON?

| Skenario | Rekomendasi |
|----------|-------------|
| Laporan capaian IKU institusi (Renstra) | **1 dashboard** pada `lakehouse.gold` saja |
| BAB IV — bukti data parity AQE OFF vs ON | **2 dashboard Superset** (atau 1 dashboard + filter schema) + query COUNT/compare |
| BAB IV — bukti performa AQE (speedup) | **Grafana Monitoring AQE** + file `metrics/` |
| User bisnis harian | Hanya **Dashboard Analitik** (`lakehouse.gold`) |

**Kesimpulan penelitian:**  
- **KPI IKU** → ukur di **Superset** (OLAP).  
- **Performa AQE** → ukur di **Grafana** (metrik).  
- **2 halaman portal KPI AQE OFF/ON** → untuk **audit salinan Gold**, bukan untuk menggandakan Monitoring Grafana.

---

## 4. Pemetaan portal Insightera

| Menu portal | Alat | Data |
|-------------|------|------|
| Dashboard Analitik | Superset | `lakehouse.gold` |
| KPI AQE OFF | Superset | `lakehouse_aqe_off.gold_aqe_off` |
| KPI AQE ON | Superset | `lakehouse_aqe_on.gold_aqe_on` |
| Dashboard Insight | Grafana | Metrik MLOps prediktif |
| Monitoring AQE | Grafana | Metrik eksperimen AQE |
| Monitoring MLOps | Grafana | Metrik DAG / training |

---

## 5. Superset: satu katalog atau tiga?

**Disarankan: tiga koneksi database** di Superset (lihat [`koneksi-trino-superset.md`](koneksi-trino-superset.md)):

1. `trino://admin@trino:8080/lakehouse` — produksi KPI  
2. `trino://admin@trino:8080/lakehouse_aqe_off` — audit OFF  
3. `trino://admin@trino:8080/lakehouse_aqe_on` — audit ON  

Alternatif: satu koneksi `lakehouse` + dataset SQL eksplisit `lakehouse.gold_aqe_off.*` — lebih murah administrasi, lebih rawan salah schema.

**Jangan** menghubungkan Superset ke Prometheus untuk KPI IKU — itu domain Grafana.

---

## 6. Implementasi yang disediakan repo

- Panduan koneksi: [`koneksi-trino-superset.md`](koneksi-trino-superset.md)
- Template dashboard duplikat OFF/ON: [`templates/07-dashboard-kpi-aqe-off-on.md`](templates/07-dashboard-kpi-aqe-off-on.md)
- Halaman portal: `portal-main/pages/dashboards/kpi-aqe-off.tsx`, `kpi-aqe-on.tsx`
- Env opsional embed: `NEXT_PUBLIC_SUPERSET_EMBED_AQE_OFF`, `NEXT_PUBLIC_SUPERSET_EMBED_AQE_ON`

Setelah dashboard Superset dibuat, tempel URL embed lewat **URL Embed** di portal.
