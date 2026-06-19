# Template 04 — Dashboard Drill-down Prodi & Fakultas (ITERA)

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)

**Hierarki Gold:** Level 0 = **42 prodi** (`prodi_id`) → Level 1 = **3 fakultas** (`fakultas_id`: FS, FTI, FTIK) → Level 2 = institusi.

---

## A. Dataset → Chart

### A1. Dataset `v_iku4_per_prodi`

SQL: [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) → **Save dataset** `v_iku4_per_prodi`.

### A2. Chart — IKU-4 per prodi (`chart_iku4_per_prodi`)

Dataset `v_iku4_per_prodi` → **Bar Chart**.

| Medan Superset | Pilih |
|----------------|-------|
| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_iku4` |
| **Dimensions** | *(kosong)* |
| **Filters** | `tahun` = `2024` *(tambah `w.tahun` di SQL dataset jika kolom belum ada)* |
| **Customize → Orientation** | **Horizontal** (nama prodi di sumbu Y) |
| **Sort** | Metric descending (prodi tertinggi di atas) |
| **Save** | `chart_iku4_per_prodi` |

### A3. Dataset `v_roll_up_fakultas`

SQL di [06](06-virtual-dataset-sql.md) → **Save dataset** `v_roll_up_fakultas`.

### A4. Chart — Roll-up fakultas (`chart_iku4_per_fakultas`)

Dataset `v_roll_up_fakultas` → **Bar Chart**.

| Medan Superset | Pilih |
|----------------|-------|
| **X-Axis** | `nama_fakultas` |
| **Y-Axis (Metrics)** | **AVG** → `avg_iku4` |
| **Dimensions** | *(kosong)* |
| **Filters** | `tahun` **=** `2024` |
| **Customize → Orientation** | **Vertical** (default) |
| **Save** | `chart_iku4_per_fakultas` |

### A5. Dashboard

| Nama | `Drill-down Prodi & Fakultas ITERA` |
| Charts | A2 + A4 |
| Filter | `tahun`, `fakultas_id`, `nama_prodi` |

---

## B. Analisis OLAP (isi setelah chart)

### Prodi fokus

| prodi_id | nama_prodi | fakultas_id | nama_fakultas |
|----------|------------|-------------|---------------|
| | | | |

### Capaian vs institusi

| IKU | Capaian prodi | Rata institusi | Selisih |
|-----|---------------|----------------|---------|
| IKU-4 | | | |

### Query analisis (SQL Lab, tidak wajib jadi dataset)

```sql
WITH institusi AS (
  SELECT AVG(persen_iku4) AS rata_iku4
  FROM lakehouse.gold.fact_iku4_kualifikasi_dosen
)
SELECT p.nama_prodi, p.nama_fakultas,
       AVG(f.persen_iku4) AS prodi_iku4, i.rata_iku4
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
CROSS JOIN institusi i
GROUP BY p.nama_prodi, p.nama_fakultas, i.rata_iku4;
```

---

## Screenshot

| File |
|------|
| superset-drilldown-prodi.png |
| superset-drilldown-fakultas.png |
