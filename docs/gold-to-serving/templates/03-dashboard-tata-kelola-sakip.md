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

### A2. Chart 1 — Trend realisasi (`chart_sakip_realisasi_line`)

Dataset `v_tata_kelola_tahun` → **Line Chart**.

| Medan Superset | Pilih |
|----------------|-------|
| **X-Axis** | `tahun` (tahun di sumbu horizontal) |
| **Y-Axis (Metrics)** | **AVG** → `persen_realisasi` |
| **Dimensions** | *(kosong)* |
| **Filters** | *(kosong)* |
| **Save** | `chart_sakip_realisasi_line` |

### A3. Chart 2 — Predikat SAKIP (`chart_sakip_predikat`)

Dataset `v_tata_kelola_tahun` → **Table**.

| Medan Superset | Pilih |
|----------------|-------|
| **Columns** | `tahun`, `predikat_sakip`, `nilai_sakip`, `persen_realisasi` |
| **Filters** | `tahun` **=** tahun terbaru (mis. `2024`) |
| **Sort** | `tahun` descending |

**Big Number** (alternatif): **Metric** = **MAX** `nilai_sakip` · **Filters** `tahun` = `2024` · subtitle manual = `predikat_sakip`.

### A4. Chart 3 — Pagu vs realisasi (`chart_sakip_pagu_realisasi`)

Dataset `v_tata_kelola_tahun` → **Bar Chart** (grouped).

| Medan Superset | Pilih |
|----------------|-------|
| **X-Axis** | `tahun` |
| **Y-Axis (Metrics)** | **SUM** → `pagu_total` **dan** **SUM** → `realisasi_total` (dua metric) |
| **Dimensions** | *(kosong)* — Superset otomatis legenda per metric |
| **Customize** | Chart orientation **Vertical** |
| **Save** | `chart_sakip_pagu_realisasi` |

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
