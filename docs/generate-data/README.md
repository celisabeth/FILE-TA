# Panduan Generate Data Staging (CSV ITERA)

Membuat **14 file CSV** di `data/staging/` sebelum pipeline Medallion (Staging → Bronze → Silver → Gold). Master data mengikuti struktur **ITERA**: 3 fakultas, **42 program studi**, dan **organisasi** kampus (Rektorat, UPA, LPPM, dll.). Skew join AQE default ke **Sains Data (SD)**.

| Skrip | Fungsi |
|-------|--------|
| [`../../scripts/generate_bronze_data.py`](../../scripts/generate_bronze_data.py) | Generator utama |
| [`../../scripts/generate_data.sh`](../../scripts/generate_data.sh) | Wrapper perintah singkat |
| [`../../scripts/count_staging_rows.py`](../../scripts/count_staging_rows.py) | Hitung baris per CSV |
| [`../../scripts/itera_reference.py`](../../scripts/itera_reference.py) | Master fakultas, prodi, organisasi |

### Struktur akademik ITERA (master)

| Fakultas | Kode | Contoh prodi |
|----------|------|----------------|
| Fakultas Sains | `FS` | Fisika (FI), Sains Data (SD), Farmasi (FA), … (10 prodi) |
| Fakultas Teknologi Industri | `FTI` | Teknik Informatika (IF), Teknik Elektro (EL), … (21 prodi) |
| Fakultas Teknologi Infrastruktur dan Kewilayahan | `FTIK` | Arsitektur (AR), Teknik Sipil (SI), PWK, … (11 prodi) |

Kolom `jurusan_id` di CSV = **kode fakultas** (kompatibilitas pipeline lama). Kolom `fakultas_id` disertakan eksplisit.

---

## 1. Kapan generate data?

| Fase penelitian | Profil disarankan | Perintah |
|-----------------|-------------------|----------|
| Uji Metadata + portal + MLOps | `metadata` | `./scripts/generate_data.sh full` |
| E2E ringan (tiga DAG, skew sedang) | `insight` | `./scripts/generate_data.sh full insight` |
| Eksperimen AQE OFF vs ON penuh | `aqe` | `./scripts/generate_data.sh full aqe` |
| Stress test cluster | `aqe-large` | `python3 scripts/generate_bronze_data.py --profile aqe-large` |
| **Tambah baris** lalu uji ulang | `append` | `./scripts/generate_data.sh append 5000` |

Setelah generate → jalankan pipeline Airflow dari [`../eksperimen/README.md`](../eksperimen/README.md).

---

## 2. Profil volume (`--profile`)

| Profil | Mahasiswa | Perkiraan total baris | Skew ke `SD` | Dipakai untuk |
|--------|-----------|------------------------|--------------|---------------|
| **`metadata`** (default) | 50.000 | ~80 ribu | tidak | Metadata, katalog, MLOps cepat |
| `dev` | 50.000 | ~80 ribu | tidak | Alias `metadata` |
| `insight` | 100.000 | ~200 ribu | 75% | E2E Insight tanpa 1M baris |
| **`aqe`** | 1.000.000 | ~1,5–2,5 juta | 75% | Hipotesis AQE shuffle/skew |
| `aqe-large` | 2.000.000 | ~3 juta+ | 80% | Stress test |

Pengali tambahan: `--scale 2.0` mengalikan target mahasiswa/dosen/dll. (contoh: `aqe` + `scale 2` ≈ 2M mahasiswa).

**Hot key skew:** `prodi_id=SD` (Sains Data) — selaras eksperimen join di Silver/Gold dan panel prodi SD di Superset.

---

## 3. Perintah cepat

```bash
cd Data-Lakehouse-Insight

# Default — metadata (~80k baris)
./scripts/generate_data.sh full

# E2E ringan + skew
./scripts/generate_data.sh full insight

# AQE penuh (~1M mahasiswa) — butuh waktu & disk lebih besar
./scripts/generate_data.sh full aqe

# Lihat rencana tanpa menulis file
./scripts/generate_data.sh dry-run aqe

# Hitung baris CSV saat ini
./scripts/generate_data.sh count

# Tambah 5.000 mahasiswa + tabel turunan (lulusan, MBKM, …)
./scripts/generate_data.sh append 5000
```

### Langsung via Python

```bash
python3 scripts/generate_bronze_data.py --mode full --profile metadata
python3 scripts/generate_bronze_data.py --profile aqe --dry-run
python3 scripts/generate_bronze_data.py --profile aqe --scale 1.5
python3 scripts/generate_bronze_data.py --profile insight --skew-fraction 0.85
python3 scripts/generate_bronze_data.py --mode append --batch-size 3000
python3 scripts/count_staging_rows.py
```

---

## 4. Opsi CLI lengkap

| Opsi | Keterangan |
|------|------------|
| `--mode full` | Overwrite semua CSV (kecuali struktur master `raw_prodi` di-refresh) |
| `--mode append` | Tambah batch ke file yang sudah ada |
| `--profile` | `metadata`, `dev`, `insight`, `aqe`, `aqe-large` |
| `--scale N` | Pengali volume di atas profil |
| `--batch-size N` | Mahasiswa baru per batch (`append`) |
| `--skew-prodi SD` | Hot key (default: Sains Data) |
| `--skew-fraction 0.75` | Fraksi baris ke prodi skew |
| `--no-skew` | Distribusi prodi merata |
| `--dry-run` | Rencana volume saja |
| `--output-dir PATH` | Ganti folder (default: `data/staging/`) |
| `--seed 42` | Reproduksibel pada `full` |

---

## 5. Output file

```
data/staging/
├── raw_fakultas.csv           # 3 baris (FS, FTI, FTIK)
├── raw_organisasi_itera.csv   # struktur organisasi kampus
├── raw_prodi.csv              # 42 program studi
├── raw_mahasiswa.csv          # volume utama
├── raw_dosen.csv
├── raw_lulusan.csv
├── raw_mbkm.csv
├── raw_penelitian.csv
├── raw_pengabdian.csv
├── raw_kegiatan_dosen.csv
├── raw_kerjasama.csv
├── raw_akreditasi.csv
├── raw_keuangan.csv
└── raw_prestasi_mahasiswa.csv
```

---

## 6. Uji ulang setelah menambah baris (`append`)

Alur disarankan saat ingin **mengulang pengujian** dengan dataset sedikit lebih besar **tanpa** menghapus seluruh CSV:

```bash
# 1. Catat baseline
python3 scripts/count_staging_rows.py > metrics/staging_rows_before.txt

# 2. Tambah batch
./scripts/generate_data.sh append 5000

# 3. Verifikasi
python3 scripts/count_staging_rows.py

# 4. Jalankan ulang pipeline (contoh urutan penuh)
docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment
docker exec lhmeta-airflow-scheduler airflow dags trigger aqe_full_experiment
docker exec lhmeta-airflow-scheduler airflow dags trigger mlops_pipeline
```

> **Catatan:** `append` menambah `mahasiswa_id` baru; pipeline Bronze/Silver/Gold perlu di-trigger ulang agar lapisan lakehouse ikut bertambah. Untuk perbandingan bersih AQE OFF vs ON, lebih aman `--mode full` lalu satu run DAG lengkap.

---

## 7. Persyaratan sumber daya

| Profil | Waktu generate | Disk CSV (perkiraan) | RAM Docker |
|--------|----------------|----------------------|------------|
| `metadata` | < 1 menit | ~10–20 MB | 8 GB |
| `insight` | 1–3 menit | ~30–60 MB | 12 GB |
| `aqe` | beberapa menit | ~150–400 MB | 16 GB+ |
| `aqe-large` | 10+ menit | ~500 MB+ | 24 GB+ |

---

## 8. Langkah berikutnya

1. `./start.sh` — naikkan stack Docker  
2. `staging_to_bronze_pipeline` — ingest ke Bronze  
3. [`../eksperimen/README.md`](../eksperimen/README.md) — Metadata → AQE → MLOps  

**Dokumen terkait:** [`../../data/README.md`](../../data/README.md) · [`../staging-to-bronze/README.md`](../staging-to-bronze/README.md) (jika ada) · template [`../eksperimen/templates/02-dataset.md`](../eksperimen/templates/02-dataset.md)
