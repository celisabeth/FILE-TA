# Pipeline 2: Bronze → Silver + Metadata Enrichment → Atlas

Panduan pipeline kedua: transformasi data Bronze (raw) menjadi Silver (cleaned & enriched) dengan metadata enrichment ke Apache Atlas.

```
Bronze (raw Iceberg)  →  Quality Check  →  Silver (enriched Iceberg)
                                                    │
                                       ┌────────────┴────────────┐
                                       │  1. Clean Metadata      │
                                       │  2. Quality Metadata    │
                                       │  3. Transform Lineage   │
                                       │  4. Business Metadata   │
                                       │  5. Compliance Metadata │
                                       └─────────────────────────┘
                                                    ↓
                                              Atlas API (S)
```

---

## Prasyarat

1. **Pipeline 1 sudah selesai** — tabel Bronze harus sudah ada di Iceberg:
   ```bash
   # Trigger pipeline 1 terlebih dahulu (jika belum)
   docker exec lhmeta-airflow-scheduler \
     airflow dags trigger staging_to_bronze_pipeline
   ```

2. **Semua service running** — cek dengan `docker ps` bahwa `lhmeta-spark-master`, `lhmeta-hive-metastore`, `lhmeta-atlas` sudah healthy.

---

## Langkah: Trigger Pipeline

### Via Airflow UI

1. Buka **http://\<ip-vm\>:18681** → login `airflow / airflow`
2. Cari DAG: **`bronze_to_silver_pipeline`**
3. Enable → Trigger DAG (▶)

### Via CLI

```bash
docker exec lhmeta-airflow-scheduler \
  airflow dags trigger bronze_to_silver_pipeline
```

---

## Apa yang Terjadi di Pipeline

### Task 1: `bronze_to_silver` (Spark ETL)

#### Quality Check

Setiap tabel Bronze dihitung quality score berdasarkan **completeness** (% non-null):

| Score | Status | Aksi |
|-------|--------|------|
| ≥ 80% | **PASS** | Tulis ke Silver ✅ |
| 60-79% | **QUARANTINE** | Tulis ke Silver, flagged ⚠️ |
| < 60% | **REJECT** | Skip, tidak ditulis ❌ |

#### Transformasi per Tabel

| Silver Table | Source Bronze | Transformasi |
|---|---|---|
| `silver_mahasiswa` | `raw_mahasiswa` + `raw_prodi` | JOIN → nama_prodi, nama_jurusan; FLAG is_mbkm (≥20 SKS luar); DEDUP |
| `silver_lulusan` | `raw_lulusan` | FLAG is_employed, is_lanjut_studi, is_wirausaha, is_terserap; DEDUP |
| `silver_dosen` | `raw_dosen` + `raw_kegiatan_dosen` | FLAG is_s3, is_praktisi, is_serdos; JOIN kegiatan → is_aktif_tridarma; DEDUP |
| `silver_penelitian_pkm` | `raw_penelitian` + `raw_pengabdian` | UNION + NORMALIZE; FLAG is_rekognisi, is_diterapkan; ADD jenis; DEDUP |
| `silver_kerjasama_aktif` | `raw_kerjasama` | FILTER status='Aktif'; FLAG is_mbkm; DEDUP |
| `silver_akreditasi_aktif` | `raw_akreditasi` | FILTER masih berlaku; WINDOW latest per prodi; FLAG is_internasional |

### Task 2: `register_silver_metadata` (Atlas Enrichment)

5 jenis metadata didaftarkan ke Atlas untuk setiap tabel Silver:

#### 1. Clean Metadata
- Schema tabel setelah enrichment (kolom baru, tipe data)
- Profiling per kolom: null_pct, completeness, distinct_count

#### 2. Quality Metadata
- Quality score dari source Bronze
- Status: PASS / QUARANTINE
- Completeness rata-rata setelah Silver cleaning

#### 3. Transformation Lineage
- Lineage: `bronze.raw_* → etl.bronze_to_silver → silver.*`
- Detail langkah transformasi (JOIN, FLAG, FILTER, UNION, DEDUP)
- Multi-source lineage (misal: silver_dosen ← raw_dosen + raw_kegiatan_dosen)

#### 4. Business Metadata
Per tabel Silver, didaftarkan:

| Table | Business Owner | IKU | Glossary Terms |
|---|---|---|---|
| `silver_mahasiswa` | Biro Akademik | IKU-2 | Mahasiswa Aktif, MBKM, SKS Luar Kampus |
| `silver_lulusan` | Pusat Karir | IKU-1 | Lulusan Terserap, Tracer Study |
| `silver_dosen` | Biro SDM | IKU-3, IKU-4 | Dosen Tetap, Tridarma, Serdos |
| `silver_penelitian_pkm` | LPPM | IKU-5 | Rekognisi Internasional, Hibah Penelitian |
| `silver_kerjasama_aktif` | Biro Kerjasama | IKU-6 | MoU, PKS, Mitra Kerjasama |
| `silver_akreditasi_aktif` | LP3M | IKU-8 | BAN-PT, Akreditasi Internasional |

#### 5. Compliance Metadata
| Table | PII | Classification | Retention | Access |
|---|---|---|---|---|
| `silver_mahasiswa` | ✅ nama, NIM, provinsi | Internal | 7 thn post-lulus | admin, akademik |
| `silver_lulusan` | ✅ NIM, perusahaan | Internal | 10 tahun | admin, karir |
| `silver_dosen` | ✅ nama, NIDN | Internal | Aktif + 5 thn | admin, sdm |
| `silver_penelitian_pkm` | ❌ | Public | Permanen | semua |
| `silver_kerjasama_aktif` | ❌ | Public | Permanen | semua |
| `silver_akreditasi_aktif` | ❌ | Public | Permanen | semua |

### Task 3: `quality_report`

Log ringkasan quality check semua tabel (parallel dengan atlas_register).

### Task 4: `verify_silver_atlas`

Verifikasi via Atlas search API bahwa Silver entities dan lineage tercatat.

---

## Verifikasi Hasil

### Atlas Web UI

1. **http://\<ip-vm\>:22100** → login `admin / admin`
2. Search: ketik `silver` → muncul 6 Silver entities
3. Klik entity → tab **Lineage** → lihat hubungan bronze → silver
4. Tab **Properties** → lihat profiling, business metadata, compliance
5. Tab **Classifications** → Silver_Layer, Quality_Pass, PII

### Atlas REST API

```bash
# Silver entities
curl -s -u admin:admin \
  "http://<ip>:22100/api/atlas/v2/search/basic" \
  -H "Content-Type: application/json" \
  -d '{"typeName":"lakehouse_dataset","classification":"Silver_Layer","limit":25}' \
  | python3 -m json.tool

# Bronze→Silver lineage processes
curl -s -u admin:admin \
  "http://<ip>:22100/api/atlas/v2/search/basic" \
  -H "Content-Type: application/json" \
  -d '{"query":"bronze_to_silver","typeName":"lakehouse_etl_process","limit":25}' \
  | python3 -m json.tool

# Detail satu entity (ambil GUID dari search)
curl -s -u admin:admin \
  "http://<ip>:22100/api/atlas/v2/entity/guid/<GUID>" \
  | python3 -m json.tool
```

### Jupyter Notebook

```python
# Lihat tabel Silver
spark.sql("SHOW TABLES IN lakehouse.silver").show()

# Query silver_mahasiswa
spark.sql("""
    SELECT prodi_id, nama_prodi, COUNT(*) as total,
           SUM(CAST(is_mbkm AS INT)) as mbkm_count
    FROM lakehouse.silver.silver_mahasiswa
    GROUP BY prodi_id, nama_prodi
    ORDER BY total DESC
""").show(25)

# Quality check: silver_dosen
spark.sql("""
    SELECT COUNT(*) as total,
           SUM(CAST(is_s3 AS INT)) as doktor,
           SUM(CAST(is_serdos AS INT)) as serdos,
           SUM(CAST(is_aktif_tridarma AS INT)) as tridarma
    FROM lakehouse.silver.silver_dosen
""").show()
```

---

## Alur Lengkap (Pipeline 1 + 2)

```bash
# Pipeline 1: Staging → Bronze
docker exec lhmeta-airflow-scheduler \
  airflow dags trigger staging_to_bronze_pipeline

# Tunggu selesai, lalu Pipeline 2: Bronze → Silver
docker exec lhmeta-airflow-scheduler \
  airflow dags trigger bronze_to_silver_pipeline
```

Setelah kedua pipeline selesai, Atlas akan memiliki:
- **24 staging+bronze entities** + **6 silver entities** = 30 total
- **12 staging→bronze lineage** + **6 bronze→silver lineage** = 18 total
- Classifications: PII, Staging_Layer, Bronze_Layer, Silver_Layer, Quality_Pass/Quarantine
- Business metadata dengan konteks IKU per tabel
- Compliance metadata dengan kebijakan retensi dan akses

---

## Arsitektur File

```
scripts/
├── spark/
│   ├── staging_to_bronze.py       ← Pipeline 1 ETL
│   └── bronze_to_silver.py        ← Pipeline 2 ETL (ini)
├── atlas/
│   ├── register_bronze_metadata.py ← Pipeline 1 Atlas
│   └── register_silver_metadata.py ← Pipeline 2 Atlas (ini)
└── dags/
    ├── staging_bronze_pipeline.py  ← DAG Pipeline 1
    └── bronze_silver_pipeline.py   ← DAG Pipeline 2 (ini)
```
