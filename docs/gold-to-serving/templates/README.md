# Template Dashboard KPI (Superset)

Setiap file berisi: **Dataset → Chart → Dashboard** (langkah Superset) + **checklist laporan**.

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
| — | [05-dashboard-mlops-prediktif.md](05-dashboard-mlops-prediktif.md) | **Grafana** (bukan Superset) |

Panduan ringkas: [../panduan-lengkap-dashboard-superset.md](../panduan-lengkap-dashboard-superset.md)

---

## Ringkas: Dataset → Chart per template

| Template | Nama dataset (contoh) | Chart type | Dashboard |
|----------|----------------------|------------|-----------|
| **01** Executive | `v_rekap_iku_tahun` | Bar (`iku_kode` × AVG capaian) | Executive IKU |
| **02** Per IKU | `ds_iku1_lulusan`, … | Bar per prodi | Detail IKU 1-8 |
| **03** SAKIP | `v_tata_kelola_tahun` | Line realisasi, Table predikat | Tata Kelola |
| **04** Prodi | `v_iku4_per_prodi`, `v_capaian_roll_up_jurusan` | Bar prodi / jurusan | Drill-down |
| **06** SQL | (semua query di atas) | — | — |
| **07** AQE | `v_rekap_iku_tahun_off/on` | Sama seperti 01 | OFF + ON |
| **05** MLOps | — | Grafana panels | Insight prediktif |

---

## Query 0 baris?

Buka [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) → bagian **Diagnosa**, lalu jalankan ulang DAG Gold.

---

## Bukan folder eksperimen

Laporan DAG/metrik BAB IV → [`../../eksperimen/templates/`](../../eksperimen/templates/)
