# Template 02 — Dashboard per Indikator IKU (IKU-1 … IKU-8)

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md) · **Peta X/Y:** [Step 3 di 00](00-alur-superset-dataset-chart.md#step-3--buat-chart)  
Satu **dataset + satu chart** per indikator (atau satu dashboard dengan banyak chart).

**Pola chart (semua IKU per prodi):** Bar horizontal — **X-Axis** = `nama_prodi` · **Metrics** = AVG kolom % IKU · **Filter** `tahun`.

---

## Pola berulang

| Step | Superset | Isi |
|------|----------|-----|
| 1 | **SQL Lab** | Query + **Save dataset** `ds_ikuN_...` |
| 2 | **Charts** → **+ Chart** | Tabel **Konfigurasi Explore** di bawah |
| 3 | **Customize** | Orientation **Horizontal** |
| 4 | **Dashboards** | Gabung `chart_iku1` … `chart_iku8` |

---

## IKU-1 — `chart_iku1_lulusan`

### Dataset `ds_iku1_lulusan`

```sql
SELECT w.tahun, p.nama_prodi, f.total_lulusan, f.lulusan_terserap,
       f.persen_terserap, f.target_iku, f.capaian_iku
FROM lakehouse.gold.fact_iku1_lulusan f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

### Konfigurasi Explore — Bar Chart (horizontal)

| Medan Superset | Pilih |
|----------------|-------|
| **Chart type** | Bar Chart |
| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_terserap` |
| **Dimensions** | *(kosong)* |
| **Filters** | `tahun` **=** `2024` |
| **Customize → Orientation** | **Horizontal** |
| **Save** | `chart_iku1_lulusan` |

---

## IKU-2 — `chart_iku2_mbkm`

### Dataset `ds_iku2_mbkm`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku2, f.mahasiswa_memenuhi_iku2, f.target_iku
FROM lakehouse.gold.fact_iku2_mbkm f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_iku2` |
| **Filters** | `tahun` = `2024` |
| **Orientation** | Horizontal |
| **Save** | `chart_iku2_mbkm` |

---

## IKU-3 — `chart_iku3_tridarma`

### Dataset `ds_iku3_dosen`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku3, f.dosen_memenuhi_iku3, f.target_iku
FROM lakehouse.gold.fact_iku3_dosen_tridarma f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_iku3` |
| **Filters** | `tahun` = `2024` |
| **Orientation** | Horizontal |
| **Save** | `chart_iku3_tridarma` |

---

## IKU-4 — `chart_iku4_dosen`

Dataset: [06](06-virtual-dataset-sql.md) → `v_iku4_per_prodi` (tambah `w.tahun` di SQL jika perlu filter tahun).

| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_iku4` |
| **Filters** | `tahun` = `2024` *(jika kolom ada di dataset)* |
| **Orientation** | Horizontal |
| **Save** | `chart_iku4_dosen` |

---

## IKU-5 — `chart_iku5_penelitian`

> Grain per fakultas: join `f.jurusan_id` = `p.fakultas_id` (FS / FTI / FTIK).

### Dataset `ds_iku5_penelitian`

```sql
SELECT w.tahun, p.fakultas_id, p.nama_fakultas,
       f.rasio_per_dosen, f.target_iku, f.capaian_iku
FROM lakehouse.gold.fact_iku5_penelitian_pkm f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.jurusan_id = p.fakultas_id;
```

| **X-Axis** | `nama_fakultas` |
| **Y-Axis (Metrics)** | **AVG** → `rasio_per_dosen` |
| **Filters** | `tahun` = `2024` |
| **Orientation** | Horizontal |
| **Save** | `chart_iku5_penelitian` |

---

## IKU-6 — `chart_iku6_kerjasama`

### Dataset `ds_iku6_kerjasama`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku6, f.target_iku
FROM lakehouse.gold.fact_iku6_kerjasama_prodi f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_iku6` |
| **Filters** | `tahun` = `2024` |
| **Orientation** | Horizontal |
| **Save** | `chart_iku6_kerjasama` |

---

## IKU-7 — `chart_iku7_mb`

### Dataset `ds_iku7_mb`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku7, f.target_iku
FROM lakehouse.gold.fact_iku7_metode_pembelajaran f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_iku7` |
| **Filters** | `tahun` = `2024` |
| **Orientation** | Horizontal |
| **Save** | `chart_iku7_mb` |

---

## IKU-8 — `chart_iku8_akreditasi`

### Dataset `ds_iku8_akreditasi`

```sql
SELECT w.tahun, p.nama_prodi, f.persen_iku8, f.target_iku
FROM lakehouse.gold.fact_iku8_akreditasi_internasional f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id;
```

| **X-Axis** | `nama_prodi` |
| **Y-Axis (Metrics)** | **AVG** → `persen_iku8` |
| **Filters** | `tahun` = `2024` |
| **Orientation** | Horizontal |
| **Save** | `chart_iku8_akreditasi` |

---

## Dashboard gabungan

| Item | Nilai |
|------|-------|
| **Dashboards** → **+ Dashboard** | `Dashboard Detail IKU 1-8` |
| Edit | Tambah `chart_iku1` … `chart_iku8` |
| **Filter dashboard** | Kolom `tahun` (scope semua chart) |

---

## Checklist isian laporan

| IKU | Dataset | Chart | X-Axis | Y-Axis (Metric) |
|-----|---------|-------|--------|-----------------|
| IKU-1 | ds_iku1_lulusan | chart_iku1_lulusan | nama_prodi | AVG persen_terserap |
| IKU-2 | ds_iku2_mbkm | chart_iku2_mbkm | nama_prodi | AVG persen_iku2 |
| … | | | | |
