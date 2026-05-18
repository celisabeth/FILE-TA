# Pipeline 1: Staging → Bronze + Metadata Ingestion → Atlas

Panduan lengkap untuk menjalankan pipeline pertama pada arsitektur Medallion Metadata Lakehouse.

```
CSV (staging)  →  Spark+Iceberg  →  Bronze (Parquet)  →  Atlas Registry
                                          │
                              ┌───────────┴───────────┐
                              │ Raw Technical Metadata │
                              │ Raw Lineage            │
                              │ Raw Data Profiling     │
                              │ Raw Classification     │
                              └────────────────────────┘
```

---

## Prasyarat

Pastikan semua service berikut sudah running:

```bash
docker compose up -d
```

| Service | Container | Port Host | Cek |
|---------|-----------|-----------|-----|
| MinIO | `lhmeta-minio` | 19000 (API), 19001 (Console) | `curl http://<ip>:19000/minio/health/live` |
| Spark Master | `lhmeta-spark-master` | 18080 (UI), 17077 | `curl http://<ip>:18080/` |
| Spark Worker 1 | `lhmeta-spark-worker-1` | — | Muncul di Spark Master UI |
| Spark Worker 2 | `lhmeta-spark-worker-2` | — | Muncul di Spark Master UI |
| Hive Metastore | `lhmeta-hive-metastore` | 19083 | `nc -z <ip> 19083` |
| Iceberg REST | `lhmeta-iceberg-rest` | 18181 | `curl http://<ip>:18181/v1/config` |
| Atlas | `lhmeta-atlas` | 22100 | `curl -u admin:admin http://<ip>:22100/api/atlas/v2/types/typedefs` |
| Airflow | `lhmeta-airflow-webserver` | 18681 | `curl http://<ip>:18681/health` |
| PostgreSQL | `lhmeta-postgres` | 15432 | `pg_isready -h <ip> -p 15432` |

---

## Langkah 1: Generate Data Staging (CSV)

Dari root project, jalankan data generator:

```bash
# Generate data awal (~78 ribu baris, ~9 MB)
python3 scripts/generate_bronze_data.py --mode full --scale 1.0

# Atau skala lebih besar untuk stress-test
python3 scripts/generate_bronze_data.py --mode full --scale 5.0
```

File CSV dihasilkan di `data/staging/`:

```
data/staging/
├── raw_mahasiswa.csv           (50.000 baris)
├── raw_lulusan.csv             ( 8.714)
├── raw_mbkm.csv                ( 7.836)
├── raw_prestasi_mahasiswa.csv  ( 5.000)
├── raw_kegiatan_dosen.csv      ( 1.994)
├── raw_penelitian.csv          ( 1.583)
├── raw_pengabdian.csv          (   855)
├── raw_dosen.csv               (   800)
├── raw_keuangan.csv            (   480)
├── raw_kerjasama.csv           (   400)
├── raw_akreditasi.csv          (    46)
└── raw_prodi.csv               (    25)
```

---

## Langkah 2: Build Custom Airflow Image

Pipeline membutuhkan Airflow dengan Java + PySpark + boto3. Build hanya perlu dilakukan **sekali**:

```bash
docker compose build airflow-init airflow-webserver airflow-scheduler
```

> Build menggunakan `airflow/Dockerfile` yang menambahkan:
> - `default-jre-headless` (Java Runtime untuk PySpark)
> - `pyspark==3.5.1`
> - `boto3` (untuk upload ke MinIO)

Setelah build selesai, restart Airflow:

```bash
docker compose up -d airflow-init airflow-webserver airflow-scheduler
```

---

## Langkah 3: Trigger Pipeline via Airflow

### Opsi A: Via Airflow Web UI

1. Buka **http://\<ip-vm\>:18681**
2. Login: `airflow` / `airflow`
3. Cari DAG: **`staging_to_bronze_pipeline`**
4. Klik toggle **Enable** (jika masih off)
5. Klik tombol **Trigger DAG** (▶)
6. Pantau progress di tab **Graph** atau **Log**

### Opsi B: Via CLI

```bash
docker exec lhmeta-airflow-scheduler \
  airflow dags trigger staging_to_bronze_pipeline
```

### Opsi C: Via REST API

```bash
curl -X POST \
  "http://<ip-vm>:18681/api/v1/dags/staging_to_bronze_pipeline/dagRuns" \
  -H "Content-Type: application/json" \
  -u "airflow:airflow" \
  -d '{"conf": {}}'
```

---

## Apa yang Terjadi di Pipeline

### Task 1: `upload_csv_to_staging`

Semua file CSV dari `data/staging/` di-upload ke MinIO bucket `staging`:

```
data/staging/raw_mahasiswa.csv  →  s3://staging/raw_mahasiswa.csv
data/staging/raw_lulusan.csv    →  s3://staging/raw_lulusan.csv
...
```

Verifikasi di MinIO Console: **http://\<ip-vm\>:19001** → bucket `staging`

### Task 2: `staging_to_bronze`

PySpark (client mode → Spark cluster) menjalankan:

1. **Baca CSV** dari `s3a://staging/raw_*.csv`
2. **Infer schema** otomatis (tipe data dari header CSV)
3. **Tulis sebagai Iceberg table** di `lakehouse.bronze.<table_name>`
   - Format: Parquet (columnar) via Iceberg
   - Lokasi: `s3a://warehouse/bronze/<table_name>/`
   - Metadata: Hive Metastore (`thrift://hive-metastore:9083`)
4. **Hitung profiling** per kolom per tabel:
   - `row_count` — jumlah baris
   - `null_count` / `null_pct` — jumlah & persentase null
   - `distinct_count` — nilai unik
   - `completeness_pct` — kelengkapan data
   - `data_type` — tipe data kolom

Verifikasi:
- Spark Master UI: **http://\<ip-vm\>:18080** → muncul completed application
- MinIO Console: folder `warehouse/bronze/` terisi Parquet files

### Task 3: `register_atlas_metadata`

Registrasi otomatis ke Apache Atlas REST API v2:

| Komponen | Apa yang didaftarkan | Jumlah |
|----------|---------------------|--------|
| **Custom Types** | `lakehouse_dataset`, `lakehouse_etl_process` | 2 entity types |
| **Classifications** | `PII`, `Bronze_Layer`, `Staging_Layer` | 3 classifications |
| **Staging Entities** | Setiap CSV file sebagai `lakehouse_dataset` | 12 entities |
| **Bronze Entities** | Setiap Iceberg table sebagai `lakehouse_dataset` + profiling | 12 entities |
| **Lineage** | `staging.raw_* → bronze.raw_*` via `lakehouse_etl_process` | 12 processes |
| **PII Tagging** | Tabel dengan kolom `nama`, `mahasiswa_id`, `dosen_id` dll | otomatis |

Metadata yang di-attach ke setiap Bronze entity:
- `schema_def` — JSON definisi kolom dan tipe data
- `profiling` — JSON profiling statistik per kolom
- `pii_columns` — daftar kolom yang mengandung PII
- `row_count`, `column_count`, `ingested_at`

### Task 4: `verify_atlas_registration`

Verifikasi via Atlas search API bahwa entities dan lineage tercatat.

---

## Verifikasi Hasil

### Cek Atlas Data Catalog

```bash
# Lihat semua lakehouse_dataset entities
curl -s -u admin:admin \
  "http://<ip-vm>:22100/api/atlas/v2/search/basic" \
  -H "Content-Type: application/json" \
  -d '{"typeName":"lakehouse_dataset","limit":25}' | python3 -m json.tool

# Lihat lineage untuk satu tabel
curl -s -u admin:admin \
  "http://<ip-vm>:22100/api/atlas/v2/search/basic" \
  -H "Content-Type: application/json" \
  -d '{"typeName":"lakehouse_etl_process","limit":25}' | python3 -m json.tool

# Lihat entity detail (ganti GUID)
curl -s -u admin:admin \
  "http://<ip-vm>:22100/api/atlas/v2/entity/bulk?typeName=lakehouse_dataset&limit=5" \
  | python3 -m json.tool
```

### Cek Atlas Web UI

1. Buka **http://\<ip-vm\>:22100**
2. Login: `admin` / `admin`
3. Search: ketik `bronze` atau `staging`
4. Klik entity → tab **Lineage** untuk melihat hubungan staging → bronze
5. Tab **Properties** untuk melihat profiling metadata
6. Tab **Classifications** untuk melihat PII / Bronze_Layer tags

### Cek Iceberg Tables via Jupyter

Buka **http://\<ip-vm\>:18888** (token: `lakehouse`), buat notebook baru:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
    .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.lakehouse.type", "hive") \
    .config("spark.sql.catalog.lakehouse.uri", "thrift://hive-metastore:9083") \
    .config("spark.sql.catalog.lakehouse.warehouse", "s3a://warehouse/") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin123") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# Lihat semua tabel Bronze
spark.sql("SHOW TABLES IN lakehouse.bronze").show()

# Query satu tabel
spark.sql("SELECT * FROM lakehouse.bronze.raw_mahasiswa LIMIT 10").show()

# Cek jumlah baris
spark.sql("SELECT COUNT(*) FROM lakehouse.bronze.raw_mahasiswa").show()
```

---

## Simulasi Incremental Update (Trigger Ulang Pipeline)

Setelah pipeline pertama berhasil, simulasikan data baru masuk:

```bash
# 1. Tambah batch data baru ke CSV staging
python scripts/generate_bronze_data.py --mode append --batch-size 2000

# 2. Trigger pipeline lagi (via CLI)
docker exec lhmeta-airflow-scheduler \
  airflow dags trigger staging_to_bronze_pipeline
```

Pipeline akan:
- Upload CSV terbaru (termasuk data append) ke MinIO
- Spark me-replace Iceberg tables dengan data lengkap
- Atlas entity ter-update dengan profiling terbaru (row_count bertambah)

---

## Troubleshooting

### Airflow DAG tidak muncul

```bash
# Cek error parsing DAG
docker exec lhmeta-airflow-scheduler \
  airflow dags list-import-errors
```

### Spark job gagal / timeout

- Cek Spark Master UI: **http://\<ip-vm\>:18080** → lihat failed applications
- Pastikan Hive Metastore running: `docker ps | grep hive`
- Pastikan MinIO accessible: `curl http://<ip-vm>:19000/minio/health/live`

### Atlas registration gagal

```bash
# Cek Atlas health
curl -u admin:admin http://<ip-vm>:22100/api/atlas/v2/system/version

# Cek Atlas logs
docker logs lhmeta-atlas --tail 50
```

### Error "database iceberg_catalog does not exist"

```bash
docker exec lhmeta-postgres \
  psql -U admin -d metastore_db -c "CREATE DATABASE iceberg_catalog;"
docker restart lhmeta-iceberg-rest
```

---

## Arsitektur File

```
Data-Lakehouse-Metadata/
├── airflow/
│   └── Dockerfile                          ← Custom Airflow + Java + PySpark
├── scripts/
│   ├── generate_bronze_data.py             ← Generator data sintetis
│   ├── dags/
│   │   ├── staging_bronze_pipeline.py      ← DAG utama pipeline
│   │   └── metadata_pipeline.py            ← DAG placeholder (legacy)
│   ├── spark/
│   │   └── staging_to_bronze.py            ← PySpark ETL: CSV → Iceberg
│   └── atlas/
│       └── register_bronze_metadata.py     ← Atlas REST API registration
├── data/
│   ├── staging/                            ← CSV files (input)
│   └── README.md                           ← Desain tabel & skema
├── conf/
│   ├── spark-defaults.conf                 ← Spark + Iceberg + S3 config
│   ├── core-site.xml                       ← Hadoop S3A config
│   └── hive-site.xml                       ← Hive Metastore config
└── docker-compose.yml                      ← Semua services
```
