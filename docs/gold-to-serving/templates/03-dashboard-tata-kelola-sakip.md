# Template — Dashboard Tata Kelola & SAKIP

**Tabel fakta:** `fact_tata_kelola` · **Dimensi:** `dim_waktu`

## Metrik utama

| Tahun | Predikat SAKIP | Nilai SAKIP | Pagu total | Realisasi | % Realisasi | Target anggaran |
|-------|----------------|-------------|------------|-----------|-------------|-----------------|
| 2021 | | | | | | |
| 2022 | | | | | | |
| 2023 | | | | | | |
| 2024 | | | | | | |
| 2025 | | | | | | |

## Panel Superset

| No | Panel | Chart | Kolom |
|----|-------|-------|-------|
| 1 | Trend realisasi anggaran | Line | `tahun`, `persen_realisasi` |
| 2 | Predikat SAKIP | Big number / table | `predikat_sakip` |
| 3 | Pagu vs realisasi | Bar grouped | `pagu_total`, `realisasi_total` |

## Query Trino

```sql
SELECT w.tahun, f.predikat_sakip, f.nilai_sakip,
       f.pagu_total, f.realisasi_total, f.persen_realisasi,
       f.target_kinerja_anggaran
FROM lakehouse.gold.fact_tata_kelola f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
ORDER BY w.tahun;
```

## Screenshot

| File |
|------|
| superset-tata-kelola.png |

## Catatan

-
