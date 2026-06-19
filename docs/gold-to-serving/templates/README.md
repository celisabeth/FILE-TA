# Template Dashboard KPI (Superset)

Setiap file berisi: **Dataset → Chart** (termasuk **X-Axis** & **Y-Axis/Metrics** di tab Data Explore) → **Dashboard** + checklist laporan.

**Data:** **15 CSV staging** (Bronze) → star schema **15 tabel Gold** (5 dim + 10 fact). Hierarki organisasi ITERA: **42 prodi** / **3 fakultas** (FS, FTI, FTIK) — lihat [`../README.md`](../README.md) §1.0.

---

## Urutan baca

| Urutan | File | Isi |
|--------|------|-----|
| 0 | [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md) | Pola umum (database, SQL Lab, chart, dashboard) |
| 1 | [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) | Semua query SQL + **diagnosa query 0 baris** |
| 2 | [01-dashboard-executive-iku.md](01-dashboard-executive-iku.md) | **Wajib** — dashboard utama 8 IKU |
| 3 | [03](03-dashboard-tata-kelola-sakip.md), [04](04-dashboard-prodi-drilldown.md) | Opsional |
| 4 | [02-dashboard-iku-per-indikator.md](02-dashboard-iku-per-indikator.md) | Opsional — satu chart per IKU |
| 5 | [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md) | Opsional penelitian AQE |
| 6 | [05-dashboard-mlops-prediktif.md](05-dashboard-mlops-prediktif.md) | **MLOps** — Superset + Grafana |
| 6b | [08-mlops-superset-sql.md](08-mlops-superset-sql.md) | SQL virtual dataset Forecast / Risk / Opportunity / Anomaly |

Panduan ringkas: [../panduan-lengkap-dashboard-superset.md](../panduan-lengkap-dashboard-superset.md)

---

## Ringkas: X-Axis & Y-Axis per template

| Template | Dataset | Chart | **X-Axis** | **Y-Axis (Metrics)** |
|----------|---------|-------|------------|----------------------|
| **01** | `v_rekap_iku_tahun` | Bar vertikal | `iku_kode` | AVG `nilai_capaian` |
| **02** | `ds_ikuN_*` | Bar horizontal | `nama_prodi` | AVG `persen_ikuN` |
| **03** | `v_tata_kelola_tahun` | Line | `tahun` | AVG `persen_realisasi` |
| **03** | sama | Bar grouped | `tahun` | SUM `pagu_total`, SUM `realisasi_total` |
| **04** | `v_iku4_per_prodi` | Bar horizontal | `nama_prodi` | AVG `persen_iku4` |
| **04** | `v_roll_up_fakultas` | Bar vertikal | `nama_fakultas` | AVG `avg_iku4` |
| **07** | `v_rekap_iku_tahun_off/on` | = template 01 | `iku_kode` | AVG `nilai_capaian` |

Peta UI Superset: [00 — Step 3](00-alur-superset-dataset-chart.md#step-3--buat-chart).

---

## Query 0 baris?

Buka [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) → bagian **Diagnosa**, lalu jalankan ulang DAG Gold.

---

## Bukan folder eksperimen

Laporan DAG/metrik BAB IV → [`../../eksperimen/templates/`](../../eksperimen/templates/)
