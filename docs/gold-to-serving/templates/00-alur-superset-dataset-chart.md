# Alur umum Superset: Database → Dataset → Chart → Dashboard

Salin pola ini ke setiap template (01–07). Bagian **khusus template** ada di file masing-masing.

**Prasyarat:** Superset jalan · **15 CSV staging** ter-generate (profil `real` / `aqe`) · DAG `metadata_full_experiment` sukses · Trino bisa query Gold (`dim_prodi` ≈ **42** baris).

---

## Step 0 — Cek data tidak kosong (Trino / SQL Lab)

Sebelum buat dataset, jalankan di **SQL Lab** (database `Lakehouse Gold (IKU)`):

```sql
SELECT COUNT(*) AS baris_rekap FROM lakehouse.gold.fact_rekap_iku_institusi;
SELECT COUNT(*) AS baris_waktu FROM lakehouse.gold.dim_waktu;
```

| Hasil | Arti | Tindakan |
|-------|------|----------|
| `baris_rekap = 0` | Tabel rekap kosong | Trigger `metadata_full_experiment` atau `silver_gold_pipeline`; tunggu task Gold selesai |
| `baris_rekap > 0` tetapi JOIN = 0 | `waktu_id` tidak cocok | Lihat query diagnosa di [06-virtual-dataset-sql.md](06-virtual-dataset-sql.md) |
| Keduanya > 0 | OK | Lanjut Step 1 |

---

## Step 1 — Koneksi DATABASE (sekali)

| Menu Superset | Aksi |
|---------------|------|
| **Settings** → **Database connections** → **+ Database** | Pilih **Trino** |
| Display name | `Lakehouse Gold (IKU)` |
| SQLAlchemy URI | `trino://admin@trino:8080/lakehouse` |
| | **Test connection** → **Save** |

(AQE OFF/ON: lihat [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md))

---

## Step 2 — Buat DATASET

### Cara A — SQL Lab (disarankan, satu dataset sudah join)

| Menu | Aksi |
|------|------|
| **SQL** → **SQL Lab** | Database = `Lakehouse Gold (IKU)` |
| Editor | Tempel SQL dari template (mis. [06](06-virtual-dataset-sql.md)) |
| | **Run** → harus ada baris (bukan “no data”) |
| Bawah hasil | **Save** → **Save dataset** |
| Dataset name | Sesuai template, mis. `v_rekap_iku_tahun` |
| | **Save** |

**Jangan** klik nama tabel di panel kiri sebelum Run (bug `record_count`).

### Cara B — Tabel fisik (layar “New dataset”)

| Menu | Aksi |
|------|------|
| **Data** → **Datasets** → **+ Dataset** | |
| **DATABASE** | `Lakehouse Gold (IKU)` |
| **SCHEMA** | `gold` |
| **TABLE** | Nama tabel di template, mis. `fact_iku4_kualifikasi_dosen` |
| | **CREATE DATASET** |

Untuk chart yang butuh join tahun, pakai **Cara A** atau buat beberapa dataset fisik + join di chart (lebih ribet).

---

## Step 3 — Buat CHART

| Menu | Aksi |
|------|------|
| **Charts** → **+ Chart** | |
| Choose a dataset | Pilih dataset Step 2 |
| Chart type | Sesuai template (Bar, Line, Table, …) |
| Tab **Data** | Isi **X-Axis**, **Metrics**, **Filters** persis seperti tabel di template (01–07) |
| Tab **Customize** | Judul, orientasi batang (horizontal/vertikal) |
| | **Save** → nama chart, mis. `chart_executive_iku_bar` |

### Peta medan Superset (tab **Data**)

Di Apache Superset 3.x/4.x:

| Label di UI Superset | Fungsi | Di template |
|----------------------|--------|-------------|
| **X-Axis** | Kategori / sumbu horizontal (batang vertikal) | **X-Axis** |
| **Metrics** | Nilai numerik (tinggi garis/batang) = **Y-Axis** visual | **Y-Axis (Metrics)** |
| **Dimensions** | Pemecah seri (batang berkelompok) | **Dimensions** |
| **Filters** | Filter tahun/prodi | **Filters** |
| **Rows / Columns** | Pivot table | **Rows** / **Columns** |

**Bar vertikal (default):**

```text
        ↑ Y ← Metrics (AVG nilai_capaian)
  ████  │
  ████  └────────────→ X-Axis (iku_kode)
```

**Bar horizontal:** isi **X-Axis** = `nama_prodi` → **Customize** → **Chart orientation** = **Horizontal** (label prodi di sumbu Y kiri).

**Line:** **X-Axis** = `tahun` · **Metrics** = nilai garis.

Setiap chart di template 01–07 punya tabel **Konfigurasi Explore**.

---

## Step 4 — Buat DASHBOARD

| Menu | Aksi |
|------|------|
| **Dashboards** → **+ Dashboard** | Nama dashboard (di template) |
| **Edit dashboard** | **+** / drag chart dari Step 3 |
| **+ Filter** (opsional) | Kolom `tahun` dari dataset |
| | **Save** |

Salin URL + `?standalone=1` → portal **URL Embed**.

---

## Step 5 — Checklist isian laporan

Setelah chart tampil benar, isi tabel kosong di file template (capaian, screenshot, catatan BAB IV).
