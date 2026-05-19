# Template Dashboard KPI (Superset)

Checklist **setelah** Anda mengikuti panduan klik Superset.

---

## Mulai di sini (wajib)

**[`../panduan-lengkap-dashboard-superset.md`](../panduan-lengkap-dashboard-superset.md)**

Ringkasannya:

1. **Settings** → **Database connections** → Trino `Lakehouse Gold (IKU)`
2. **SQL Lab** → query → **Save dataset** `v_rekap_iku_tahun`
3. **Charts** → bar chart dari dataset itu
4. **Dashboards** → susun + embed portal

Layar **Data → Datasets → + Dataset** dipakai jika Anda memilih **tabel fisik**; untuk Executive IKU lebih mudah lewat **SQL Lab** (file [06](06-virtual-dataset-sql.md)).

---

## File di folder ini

| File | Dipakai pada langkah panduan |
|------|------------------------------|
| [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) | Langkah 2 — salin SQL |
| [01-dashboard-executive-iku.md](01-dashboard-executive-iku.md) | Langkah 3–4 — panel chart |
| [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md) | §6 opsional AQE |
| [02](02-dashboard-iku-per-indikator.md)–[04](04-dashboard-prodi-drilldown.md) | Opsional |
| [05-dashboard-mlops-prediktif.md](05-dashboard-mlops-prediktif.md) | Grafana (bukan Superset) |

---

## Bukan folder eksperimen

Laporan runtime DAG / metrik BAB IV → [`../../eksperimen/templates/`](../../eksperimen/templates/)
