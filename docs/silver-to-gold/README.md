# Pipeline 3: Silver → Gold (Star Schema + Metadata Enrichment)

## Arsitektur Pipeline

```
Silver (Enriched)
  ├── silver_mahasiswa       ─┐
  ├── silver_lulusan         ─┤
  ├── silver_dosen           ─┤    ┌──────────────────────┐     ┌─────────────┐
  ├── silver_penelitian_pkm  ─┼──→ │ PySpark Star Schema  │ ──→ │ GOLD LAYER  │
  ├── silver_kerjasama_aktif ─┤    │ Transform + Aggregate│     │ (Iceberg)   │
  └── silver_akreditasi_aktif┘    └──────────────────────┘     └──────┬──────┘
                                                                       │
                                               ┌───────────────────────┘
                                               ▼
                                   ┌──────────────────────┐     ┌─────────────┐
                                   │ Atlas Gold Metadata  │ ──→ │ Portal Data │
                                   │ Registration         │     │ Catalog     │
                                   └──────────────────────┘     └─────────────┘
```

## Star Schema Design

### Dimensi (5 tabel)

| Tabel | Sumber | Deskripsi |
|-------|--------|-----------|
| `dim_waktu` | Generated | Tahun 2020-2025, 12 bulan, semester, triwulan |
| `dim_prodi` | raw_prodi | Program studi + jurusan + fakultas |
| `dim_dosen` | silver_dosen | Profil dosen + kualifikasi (S3, serdos, praktisi) |
| `dim_mahasiswa` | silver_mahasiswa | Profil mahasiswa + demografi |
| `dim_topik_penelitian` | Generated | 4 topik: Sustainable Energy, Innovative Industry, Green Infra, Community Dev |

### Fakta IKU (10 tabel)

| Tabel | IKU | Sumber | Metrik Utama |
|-------|-----|--------|--------------|
| `fact_iku1_lulusan` | IKU-1 | silver_lulusan | % lulusan bekerja/studi/wirausaha |
| `fact_iku2_mbkm` | IKU-2 | silver_mahasiswa + raw_prestasi | % mahasiswa ≥20 SKS luar / prestasi nasional |
| `fact_iku3_dosen_tridarma` | IKU-3 | silver_dosen + raw_kegiatan | % dosen tridarma luar/praktisi/bina prestasi |
| `fact_iku4_kualifikasi_dosen` | IKU-4 | silver_dosen | % dosen S3/sertifikat/praktisi |
| `fact_iku5_penelitian_pkm` | IKU-5 | silver_penelitian_pkm + silver_dosen | Rasio output intl per dosen |
| `fact_iku6_kerjasama_prodi` | IKU-6 | silver_kerjasama_aktif + raw_prodi | % prodi bekerjasama mitra |
| `fact_iku7_metode_pembelajaran` | IKU-7 | raw_prodi (simulasi) | % MK case method / team-based |
| `fact_iku8_akreditasi_intl` | IKU-8 | silver_akreditasi_aktif + raw_prodi | % prodi akreditasi internasional |
| `fact_tata_kelola` | SAKIP | raw_keuangan | Predikat SAKIP, kinerja anggaran |
| `fact_rekap_iku_institusi` | All | Agregat dari fakta IKU 1–8 yang berhasil ditulis | Executive summary per tahun |

## Gold Metadata (5 Kategori)

Berdasarkan diagram arsitektur Bigdata Pipeline Metadata:

### 1. Business Metadata
- **Definisi KPI**: Formula, sumber renstra, sasaran strategis
- **Star Schema Relationships**: FK references antar dim–fact
- **Ownership**: Penanggung jawab (Wakil Rektor I/II/III/IV, LP3M, LPPM)

### 2. KPI Metadata
- **Target per tahun**: Dari Renstra ITERA 2020-2024
- **Capaian aktual**: Dihitung dari data Silver
- **Status**: Tercapai / On Track / Tidak Tercapai
- **Formula**: Cara menghitung setiap IKU

### 3. AI Metadata
- **ML Readiness**: Apakah tabel fact siap untuk ML
- **Feature Store Candidate**: Tabel yang bisa dijadikan feature
- **Suggested Models**: trend_analysis, anomaly_detection

### 4. Consumption Metadata
- **Consumers**: Siapa yang menggunakan (Rektor, Senat, dll)
- **Dashboard Panel**: Lokasi di Executive Dashboard
- **OLAP Role**: Dimension drill atau Fact metrics

### 5. Advanced Lineage
- **Full chain**: Staging → Bronze → Silver → Gold (end-to-end)
- **Multi-source lineage**: Satu fact bisa dari banyak Silver/Bronze tables
- **Transform description**: Aggregasi, join, formula yang digunakan

## Atlas Classifications (Gold)

| Classification | Deskripsi |
|---------------|-----------|
| `Gold_Layer` | Semua tabel di Gold layer |
| `Star_Schema_Dimension` | Tabel dimensi |
| `Star_Schema_Fact` | Tabel fakta |
| `KPI_Metric` | Tabel berisi metrik KPI/IKU |
| `Executive_Dashboard` | Data untuk Dashboard Pimpinan |

## Target IKU (Renstra ITERA 2020-2024)

| IKU | Indikator | 2021 | 2022 | 2023 | 2024 | 2025 |
|-----|-----------|------|------|------|------|------|
| IKU-1 | % Lulusan terserap | 75% | 76% | 77% | 78% | 80% |
| IKU-2 | % Mahasiswa MBKM/prestasi | 20% | 25% | 30% | 35% | 40% |
| IKU-3 | % Dosen tridarma luar | 15% | 17% | 20% | 25% | 30% |
| IKU-4 | % Dosen S3/sertifikat | 30% | 32% | 40% | 50% | 55% |
| IKU-5 | Rasio output intl/dosen | 0.10 | 0.15 | 0.20 | 0.25 | 0.30 |
| IKU-6 | % Prodi bermitra | 35% | 40% | 50% | 60% | 65% |
| IKU-7 | % MK inovatif | 25% | 30% | 35% | 40% | 45% |
| IKU-8 | % Prodi akreditasi intl | 2.5% | 2.5% | 2.5% | 3.0% | 5.0% |

## File & Script

```
scripts/
├── spark/
│   └── silver_to_gold.py       ← PySpark ETL star schema
├── atlas/
│   └── register_gold_metadata.py  ← Atlas Gold metadata registration
└── dags/
    └── silver_gold_pipeline.py ← Airflow DAG
```

## Menjalankan Pipeline

### 1. Pastikan Silver layer sudah siap

```bash
# Verifikasi tabel Silver ada
docker exec lhmeta-spark-master spark-sql \
  --conf spark.sql.catalog.lakehouse=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.lakehouse.type=hive \
  --conf spark.sql.catalog.lakehouse.uri=thrift://hive-metastore:9083 \
  -e "SHOW TABLES IN lakehouse.silver"
```

### 2. Trigger DAG via Airflow

```bash
# Via UI
# Buka http://localhost:8080 → DAGs → silver_to_gold_pipeline → Trigger

# Via CLI
docker exec lhmeta-airflow-webserver \
  airflow dags trigger silver_to_gold_pipeline
```

### 3. Verifikasi Gold layer

```bash
# Daftar tabel Gold
docker exec lhmeta-spark-master spark-sql \
  --conf spark.sql.catalog.lakehouse=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.lakehouse.type=hive \
  --conf spark.sql.catalog.lakehouse.uri=thrift://hive-metastore:9083 \
  -e "SHOW TABLES IN lakehouse.gold"

# Cek rekap IKU
docker exec lhmeta-spark-master spark-sql \
  --conf spark.sql.catalog.lakehouse=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.lakehouse.type=hive \
  --conf spark.sql.catalog.lakehouse.uri=thrift://hive-metastore:9083 \
  -e "SELECT iku_kode, iku_nama, nilai_capaian, nilai_target, status_capaian
      FROM lakehouse.gold.fact_rekap_iku_institusi
      WHERE waktu_id = 202412
      ORDER BY iku_kode"
```

### 4. Verifikasi Atlas metadata

```bash
# Gold entities
curl -s -u admin:admin \
  "http://localhost:21000/api/atlas/v2/search/basic" \
  -H "Content-Type: application/json" \
  -d '{"typeName":"lakehouse_dataset","classification":"Gold_Layer","limit":50}' | \
  python3 -m json.tool

# KPI metrics
curl -s -u admin:admin \
  "http://localhost:21000/api/atlas/v2/search/basic" \
  -H "Content-Type: application/json" \
  -d '{"typeName":"lakehouse_dataset","classification":"KPI_Metric","limit":50}' | \
  python3 -m json.tool

# Full lineage (satu tabel)
GUID=$(curl -s -u admin:admin \
  "http://localhost:21000/api/atlas/v2/entity/uniqueAttribute/type/lakehouse_dataset?attr:qualifiedName=gold.fact_iku1_lulusan@lakehouse" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['entity']['guid'])")

curl -s -u admin:admin \
  "http://localhost:21000/api/atlas/v2/lineage/${GUID}?depth=5&direction=BOTH" | \
  python3 -m json.tool
```

## Troubleshooting

### Error: Table silver.silver_* not found
Silver pipeline belum dijalankan. Jalankan `bronze_to_silver_pipeline` terlebih dahulu.

### Error: Atlas type already exists (409)
Ini normal — tipe sudah dibuat oleh pipeline sebelumnya. Script akan mengabaikan error 409.

### Error: SparkSession timeout
Spark cluster mungkin belum siap. Cek `docker logs lhmeta-spark-master` dan pastikan worker sudah terdaftar.

### Gold layer kosong (0 rows)
Cek Silver layer terlebih dahulu. Beberapa fact table bergantung pada data yang cukup di Silver.

## Pipeline Lengkap — Full Medallion

```
Pipeline 1: Staging → Bronze
  CSV → Iceberg
  Metadata: Technical, Lineage, Profiling, Classification

Pipeline 2: Bronze → Silver
  Raw → Enriched + Quality
  Metadata: Clean, Quality, Transform Lineage, Business, Compliance

Pipeline 3: Silver → Gold  ← anda di sini
  Enriched → Star Schema (5 dim + 10 fact)
  Metadata: Business, KPI, AI, Consumption, Advanced Lineage

Next: Gold → Serving (Trino, Superset, dashboard KPI)
  → docs/gold-to-serving/README.md
```

## Contoh Query OLAP (untuk Dashboard Pimpinan)

```sql
-- Capaian IKU per tahun
SELECT
  w.tahun, r.iku_kode, r.iku_nama,
  r.nilai_capaian, r.nilai_target, r.status_capaian
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
ORDER BY w.tahun, r.iku_kode;

-- IKU-1 per prodi
SELECT
  p.nama_prodi, p.jenjang,
  f.total_lulusan, f.persen_terserap, f.target_iku, f.capaian_iku
FROM lakehouse.gold.fact_iku1_lulusan f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
ORDER BY f.capaian_iku DESC;

-- IKU-4 kualifikasi dosen per prodi
SELECT
  p.nama_prodi, p.nama_jurusan,
  f.total_dosen_tetap, f.dosen_s3, f.dosen_sertifikat_industri,
  f.persen_iku4, f.target_iku
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
ORDER BY p.nama_jurusan, f.persen_iku4 DESC;
```
