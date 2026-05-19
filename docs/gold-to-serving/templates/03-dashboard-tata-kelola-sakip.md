# Template 03 — Dashboard Tata Kelola & SAKIP

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)

---

## A. Dataset → Chart

### A1. Dataset `v_tata_kelola_tahun`

| Menu | Aksi |
|------|------|
| **SQL Lab** | Database `Lakehouse Gold (IKU)` |

```sql
SELECT w.tahun, f.predikat_sakip, f.nilai_sakip,
       f.pagu_total, f.realisasi_total, f.persen_realisasi,
       f.target_kinerja_anggaran
FROM lakehouse.gold.fact_tata_kelola f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
ORDER BY w.tahun;
```

**Save dataset** → `v_tata_kelola_tahun`.

### A2. Chart 1 — Trend realisasi anggaran

| Wizard | Isi |
|--------|-----|
| Dataset | `v_tata_kelola_tahun` |
| Chart type | **Line Chart** |
| Dimension | `tahun` |
| Metric | **AVG** `persen_realisasi` |
| Save | `chart_sakip_realisasi_line` |

### A3. Chart 2 — Predikat SAKIP

| Chart type | **Table** atau **Big Number** |
| Dimension | `tahun` |
| Columns / Metric | `predikat_sakip`, `nilai_sakip` |
| Save | `chart_sakip_predikat` |

### A4. Chart 3 — Pagu vs realisasi

| Chart type | **Bar Chart** (grouped) |
| Dimension | `tahun` |
| Metrics | **SUM** `pagu_total`, **SUM** `realisasi_total` |
| Save | `chart_sakip_pagu_realisasi` |

### A5. Dashboard

| Item | Nilai |
|------|-------|
| Nama | `Tata Kelola & SAKIP` |
| Charts | A2 + A3 + A4 |
| Bisa digabung ke dashboard [01](01-dashboard-executive-iku.md) |

---

## B. Checklist isian laporan

| Tahun | Predikat SAKIP | % Realisasi | |
|-------|----------------|-------------|---|
| 2024 | | | |

### Screenshot

| File |
|------|
| superset-tata-kelola.png |

### Catatan

-
