# Template 02 — Dashboard per Indikator IKU (IKU-1 … IKU-8)

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)  
Satu **dataset + satu chart** per indikator (atau satu dashboard dengan banyak tab/chart).

---

## Pola berulang (setiap IKU)

| Step | Superset | Isi |
|------|----------|-----|
| 1 | **SQL Lab** | Query ke `fact_ikuN_*` + join `dim_waktu` / `dim_prodi` |
| 2 | **Save dataset** | Nama `ds_ikuN_...` |
| 3 | **Charts** → **+ Chart** | Bar chart |
| 4 | **Dashboards** | Gabung semua chart IKU |

---

## IKU-1 — `fact_iku1_lulusan`

### Dataset `ds_iku1_lulusan`

```sql
SELECT w.tahun, p.nama_prodi, f.total_lulusan, f.lulusan_terserap,
       f.persen_terserap, f.target_iku, f.capaian_iku
FROM lakehouse.gold.fact_iku1_lulusan f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

### Chart

| Field | Nilai |
|-------|-------|
| Dataset | `ds_iku1_lulusan` |
| Type | **Bar Chart** (horizontal) |
| Dimension | `nama_prodi` |
| Metric | **AVG** `persen_terserap` |
| Filter | `tahun` = 2024 |
| Save as | `chart_iku1_lulusan` |

---

## IKU-2 — `fact_iku2_mbkm`

### Dataset `ds_iku2_mbkm`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku2, f.mahasiswa_memenuhi_iku2, f.target_iku
FROM lakehouse.gold.fact_iku2_mbkm f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

### Chart

| Dimension | `nama_prodi` |
| Metric | **AVG** `persen_iku2` |
| Save as | `chart_iku2_mbkm` |

---

## IKU-3 — `fact_iku3_dosen_tridarma`

### Dataset `ds_iku3_dosen`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku3, f.dosen_memenuhi_iku3, f.target_iku
FROM lakehouse.gold.fact_iku3_dosen_tridarma f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

### Chart

| Metric | **AVG** `persen_iku3` |
| Save as | `chart_iku3_tridarma` |

---

## IKU-4 — `fact_iku4_kualifikasi_dosen`

Gunakan query lengkap di [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) → dataset `v_iku4_per_prodi`.

| Metric | **AVG** `persen_iku4` |
| Save as | `chart_iku4_dosen` |

---

## IKU-5 — `fact_iku5_penelitian_pkm`

> Join via `jurusan_id`, bukan `prodi_id`.

### Dataset `ds_iku5_penelitian`

```sql
SELECT w.tahun, p.nama_jurusan, f.rasio_per_dosen, f.target_iku, f.capaian_iku
FROM lakehouse.gold.fact_iku5_penelitian_pkm f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.jurusan_id = p.nama_jurusan
   OR f.jurusan_id = p.prodi_id;
```

*(Sesuaikan join dengan kolom aktual di Gold Anda.)*

### Chart

| Dimension | `nama_jurusan` |
| Metric | **AVG** `rasio_per_dosen` |

---

## IKU-6 — `fact_iku6_kerjasama_prodi`

### Dataset `ds_iku6_kerjasama`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku6, f.target_iku
FROM lakehouse.gold.fact_iku6_kerjasama_prodi f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

### Chart

| Metric | **AVG** `persen_iku6` |

---

## IKU-7 — `fact_iku7_metode_pembelajaran`

### Dataset `ds_iku7_mb`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku7, f.target_iku
FROM lakehouse.gold.fact_iku7_metode_pembelajaran f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

---

## IKU-8 — `fact_iku8_akreditasi_internasional`

### Dataset `ds_iku8_akreditasi`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku8, f.target_iku
FROM lakehouse.gold.fact_iku8_akreditasi_internasional f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

---

## Dashboard gabungan

| Item | Nilai |
|------|-------|
| **Dashboards** → **+ Dashboard** | `Dashboard Detail IKU 1-8` |
| Edit | Tambah `chart_iku1` … `chart_iku8` |
| Filter global | `tahun` |

---

## Checklist isian laporan

| IKU | Dataset | Chart | Screenshot |
|-----|---------|-------|------------|
| IKU-1 | ds_iku1_lulusan | chart_iku1_lulusan | |
| IKU-2 | | | |
| … | | | |
