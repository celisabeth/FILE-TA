# Template — Dashboard Executive IKU (Pimpinan)

> **Panduan langkah demi langkah:** [../panduan-lengkap-dashboard-superset.md](../panduan-lengkap-dashboard-superset.md) (§ Langkah C)  
> Duplikat untuk AQE OFF/ON: [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md)

**Alat:** Apache Superset · **Schema:** `lakehouse.gold` (atau `gold_aqe_off` / `gold_aqe_on` untuk audit AQE)

## Identitas dashboard

| Item | Nilai |
|------|-------|
| Nama dashboard | Executive IKU ITERA |
| URL Superset | http://localhost:18089 |
| Dataset utama | `fact_rekap_iku_institusi` ⋈ `dim_waktu` |
| Periode laporan | Tahun: _____ |

## Panel KPI (isi dari Superset / Trino)

| No | IKU | Indikator | Capaian | Target | Status | Chart |
|----|-----|-----------|---------|--------|--------|-------|
| 1 | IKU-1 | Lulusan terserap | | % | | Bar / bullet |
| 2 | IKU-2 | MBKM / prestasi nasional | | % | | |
| 3 | IKU-3 | Dosen tridarma luar | | % | | |
| 4 | IKU-4 | Kualifikasi dosen | | % | | |
| 5 | IKU-5 | Output intl per dosen | | rasio | | |
| 6 | IKU-6 | Prodi bermitra | | % | | |
| 7 | IKU-7 | MK inovatif | | % | | |
| 8 | IKU-8 | Akreditasi internasional | | % | | |
| 9 | SAKIP | Predikat tata kelola | | BB/A | | Table |
| 10 | Anggaran | Kinerja anggaran | | % | | Line |

## Filter global

| Filter | Nilai dipilih |
|--------|---------------|
| `dim_waktu.tahun` | |
| `dim_prodi.nama_jurusan` | Semua / JTK / JSA / … |

## Query verifikasi (Trino)

```sql
SELECT w.tahun, r.iku_kode, r.nilai_capaian, r.nilai_target, r.status_capaian
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
WHERE w.tahun = 2024
ORDER BY r.iku_kode;
```

## Screenshot

| No | File |
|----|------|
| 1 | superset-executive-iku-overview.png |
| 2 | superset-executive-iku-heatmap.png |

## Catatan pembahasan

-
