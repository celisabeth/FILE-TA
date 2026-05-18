# Template — Dashboard Drill-down Prodi / Jurusan

Demonstrasi operasi OLAP **drill-down** dan **roll-up** pada star schema Gold.

## Hierarki yang digunakan

| Dimensi | Level 0 → Level 3 |
|---------|-------------------|
| Organisasi | Prodi → Jurusan → Fakultas → Institusi |
| Waktu | Bulan → Triwulan → Semester → Tahun |

## Prodi fokus analisis

| Item | Nilai |
|------|-------|
| `prodi_id` | |
| `nama_prodi` | |
| `nama_jurusan` | |

## Capaian IKU prodi vs rata institusi

| IKU | Capaian prodi | Rata institusi | Selisih | Status |
|-----|---------------|----------------|---------|--------|
| IKU-1 | | | | |
| IKU-4 | | | | |
| IKU-7 | | | | |

## Drill-down waktu (contoh IKU-4)

| Level waktu | Filter / GROUP BY | Nilai capaian |
|-------------|-------------------|---------------|
| Tahun 2024 | `w.tahun = 2024` | |
| Triwulan IV | `w.triwulan = 4` | |
| Desember | `w.bulan = 12` | |

## Query — prodi vs institusi (IKU-4)

```sql
WITH institusi AS (
  SELECT AVG(persen_iku4) AS rata_iku4
  FROM lakehouse.gold.fact_iku4_kualifikasi_dosen
)
SELECT p.nama_prodi, f.persen_iku4, i.rata_iku4,
       f.persen_iku4 - i.rata_iku4 AS selisih
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
CROSS JOIN institusi i
WHERE p.prodi_id = 'SD';
```

## Screenshot

| File |
|------|
| superset-drilldown-prodi-sd.png |
