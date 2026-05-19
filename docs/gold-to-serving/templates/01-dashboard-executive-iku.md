# Template 01 — Dashboard Executive IKU (8 indikator + SAKIP)

**Alat:** Superset · **Schema:** `lakehouse.gold`  
**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)

---

## A. Dataset → Chart (langkah ini)

### A1. Dataset utama (SQL Lab)

| Item | Nilai |
|------|-------|
| Menu | **SQL** → **SQL Lab** |
| Database | `Lakehouse Gold (IKU)` |
| Nama dataset | `v_rekap_iku_tahun` |

**SQL** (salin → **Run** → harus > 0 baris):

```sql
SELECT w.tahun, r.iku_kode, r.iku_nama,
       r.nilai_capaian, r.nilai_target, r.satuan, r.status_capaian
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
ORDER BY w.tahun, r.iku_kode;
```

Jika **0 baris** → [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) bagian diagnosa.

**Simpan:** **Save** → **Save dataset** → nama `v_rekap_iku_tahun`.

### A2. Dataset SAKIP (opsional, SQL Lab)

| Nama dataset | `v_tata_kelola_tahun` |
| SQL | lihat [03-dashboard-tata-kelola-sakip.md](03-dashboard-tata-kelola-sakip.md) |

### A3. Chart — Bar 8 IKU

| Wizard | Isi |
|--------|-----|
| **Charts** → **+ Chart** | |
| Dataset | `v_rekap_iku_tahun` |
| Chart type | **Bar Chart** |
| Dimension | `iku_kode` |
| Metric | **AVG** `nilai_capaian` |
| Filter | `tahun` = `2024` (sesuaikan) |
| Save chart | `chart_executive_iku_bar` |

### A4. Chart — Heatmap / tabel status (opsional)

| Dataset | `v_rekap_iku_tahun` |
| Chart type | **Pivot table** atau **Table** |
| Rows | `iku_kode` |
| Columns | `status_capaian` atau banding `nilai_capaian` vs `nilai_target` |

### A5. Chart — Anggaran / SAKIP (opsional)

| Dataset | `v_tata_kelola_tahun` |
| Chart type | **Line Chart** |
| Dimension | `tahun` |
| Metric | **AVG** `persen_realisasi` |

### A6. Dashboard

| Item | Nilai |
|------|-------|
| **Dashboards** → **+ Dashboard** | `Executive IKU ITERA — Lakehouse Gold` |
| Edit | Tambah chart A3 (+ A4, A5) |
| Filter | `tahun` dari `v_rekap_iku_tahun` |
| Portal embed | `/dashboards/analitik` |

---

## B. Checklist isian laporan (setelah chart jadi)

| Item | Nilai |
|------|-------|
| Nama dashboard | Executive IKU ITERA |
| URL Superset | http://103.174.114.177:18089 |
| Periode | Tahun: _____ |

### Panel KPI (isi angka dari chart / export CSV)

| No | IKU | Capaian | Target | Status | Chart ID |
|----|-----|---------|--------|--------|----------|
| 1 | IKU-1 | | | | `chart_executive_iku_bar` |
| 2 | IKU-2 | | | | |
| … | … | | | | |
| 8 | IKU-8 | | | | |
| 9 | SAKIP | | | | |
| 10 | Anggaran | | | | line SAKIP |

### Screenshot

| File |
|------|
| superset-executive-iku-overview.png |
| superset-executive-iku-heatmap.png |

### Catatan pembahasan

-
