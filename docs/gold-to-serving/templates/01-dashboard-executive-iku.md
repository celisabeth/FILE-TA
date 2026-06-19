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

### A3. Chart — Bar 8 IKU (`chart_executive_iku_bar`)

**Charts** → **+ Chart** → dataset `v_rekap_iku_tahun` → **Bar Chart**.

#### Konfigurasi Explore (tab **Data**)

| Medan Superset | Pilih |
|----------------|-------|
| **X-Axis** | `iku_kode` (IKU-1 … IKU-8 di sumbu bawah) |
| **Y-Axis (Metrics)** | **+ Metric** → **AVG** → `nilai_capaian` |
| **Dimensions** | *(kosong)* |
| **Filters** | `tahun` **Equal to** `2024` (sesuaikan tahun di data) |
| **Sort by** | `iku_kode` ascending |
| **Row limit** | 100 (default) |

#### Customize (opsional)

| Medan | Nilai |
|-------|-------|
| Chart title | Capaian IKU Institusi |
| Chart orientation | **Vertical** |
| Show value on chart | Aktif (angka di atas batang) |

**Save** → `chart_executive_iku_bar`.

### A4. Chart — Tabel status (opsional, `chart_executive_iku_table`)

Dataset `v_rekap_iku_tahun` → **Table**.

| Medan Superset | Pilih |
|----------------|-------|
| **Columns** | `tahun`, `iku_kode`, `iku_nama`, `nilai_capaian`, `nilai_target`, `status_capaian` |
| **Filters** | `tahun` = `2024` |
| **Sort** | `iku_kode` ascending |

**Pivot table** (alternatif): **Rows** `iku_kode` · **Columns** `status_capaian` · **Metrics** `COUNT(*)` atau **AVG** `nilai_capaian`.

### A5. Chart — SAKIP realisasi (opsional, `chart_executive_sakip_line`)

Dataset `v_tata_kelola_tahun` → **Line Chart**.

| Medan Superset | Pilih |
|----------------|-------|
| **X-Axis** | `tahun` |
| **Y-Axis (Metrics)** | **AVG** → `persen_realisasi` |
| **Dimensions** | *(kosong)* |
| **Filters** | *(kosong, atau batasi rentang tahun)* |

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
