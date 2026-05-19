# Template 04 — Dashboard Drill-down Prodi / Jurusan

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)

---

## A. Dataset → Chart

### A1. Dataset `v_iku4_per_prodi`

SQL: [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) → **Save dataset** `v_iku4_per_prodi`.

### A2. Chart — IKU-4 per prodi

| Wizard | Isi |
|--------|-----|
| Dataset | `v_iku4_per_prodi` |
| Chart type | **Bar Chart** |
| Dimension | `nama_prodi` |
| Metric | **AVG** `persen_iku4` |
| Filter | `tahun` (tambah kolom tahun di SQL jika belum ada) |
| Save | `chart_iku4_per_prodi` |

### A3. Dataset `v_capaian_roll_up_jurusan`

SQL di [06](06-virtual-dataset-sql.md) → **Save dataset** `v_capaian_roll_up_jurusan`.

### A4. Chart — Roll-up jurusan

| Dimension | `nama_jurusan` |
| Metric | **AVG** `avg_iku4` |
| Filter | `tahun` = 2024 |
| Save | `chart_iku4_per_jurusan` |

### A5. Dashboard

| Nama | `Drill-down Prodi & Jurusan` |
| Charts | A2 + A4 |
| Filter | `tahun`, `nama_prodi` |

---

## B. Analisis OLAP (isi setelah chart)

### Prodi fokus

| prodi_id | nama_prodi | nama_jurusan |
|----------|------------|--------------|
| | | |

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
SELECT p.nama_prodi, AVG(f.persen_iku4) AS prodi_iku4, i.rata_iku4
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
CROSS JOIN institusi i
GROUP BY p.nama_prodi, i.rata_iku4;
```

---

## Screenshot

| File |
|------|
| superset-drilldown-prodi.png |
