# Data Lakehouse Insight

## Implementasi Pipeline Big Data Berbasis Arsitektur Data Lakehouse dan MLOps untuk Integrasi Data Perguruan Tinggi

Repositori ini berisi implementasi pipeline big data terintegrasi untuk lingkungan perguruan tinggi, menggabungkan arsitektur **Data Lakehouse** (Medallion Bronze–Silver–Gold, Apache Iceberg, governance metadata), **Adaptive Query Execution (AQE)**, **analitik & serving** (Trino, Superset, Grafana), serta **MLOps** (MLflow, empat use case prediktif: Forecast, Risk Score, Opportunity, Anomalies) melalui portal **Insightera** (`portal-main`).

### Tujuan penelitian

1. **Merancang** arsitektur dan pipeline big data berbasis Data Lakehouse dan MLOps untuk integrasi data perguruan tinggi serta **mengukur kinerja** pipeline berdasarkan metrik performa dan kualitas data.
2. **Mengimplementasikan** pipeline big data berbasis Data Lakehouse dan MLOps untuk mendukung integrasi, pengolahan, dan analitik data perguruan tinggi.
3. **Melakukan evaluasi komparatif** terhadap implementasi pipeline berdasarkan aspek performa, kualitas data, skalabilitas, dan efektivitas integrasi data.

---

## Tech Stack (ringkas)

| Kelompok | Teknologi |
|----------|-----------|
| Orkestrasi | Docker Compose, Airflow 2.9.1 |
| Data | Spark 3.5.1, Iceberg 1.5.2, MinIO, Hive Metastore |
| Metadata | Atlas 2.3.0, HBase, Solr, Kafka, Next.js Catalog |
| AQE / Serving | Trino, Superset, Prometheus, Grafana |
| MLOps | MLflow, scikit-learn, PySpark features |
| Metrik | `metrics/` (JSON eksperimen) |

---

## 1. Rancangan penelitian — tiga pipeline

### 1.1 Pipeline gabungan — Metadata + AQE + MLOps

Diagram integrasi end-to-end (sumber: `MLOps-pipeline.png`):

![Pipeline gabungan Metadata, AQE, dan MLOps](./MLOps-pipeline.png)

**Alur utama (sesuai anotasi diagram):**

| Tahap | Proses | Output / metadata |
|-------|--------|-------------------|
| 1 | **Gold** Medallion terisi (star schema IKU) | Tabel `lakehouse.gold.*` di Iceberg |
| 2 | **Query Engine** (Trino/Spark + AQE) ↔ Gold | Dashboard Insight (Superset); metrik query |
| 3 | **Inference Data** diambil dari Gold | View/tabel siap ML |
| 4 | **Data Preprocessing** → **Feature Data** | Parquet di `s3a://mlops/features/` |
| 5 | **Data Processing** → **Modeling** (Train) | Model + **Metadata Gold-Development** |
| 6 | **GM: Gold-MLOps** (MLflow Registry) | Artifact + versi model |
| 7 | **MLOPS Engine** | Forecast · Risk Score · Opportunity · Anomalies |
| 8 | **Output Tables** + **Metadata MLOps** | Iceberg Gold + entitas Atlas |
| 9 | **Atlas API** | Governance terpusat (lineage 1 & 2 di diagram) |

**DAG Airflow terkait:** `metadata_full_experiment` → `aqe_full_experiment` → `mlops_pipeline` (urutan disarankan setelah Gold terisi).

---

### 1.2 Pipeline Metadata — Medallion & Apache Atlas

Diagram khusus metadata (sumber: `Bigdata-pipeline-Metadata.jpg`):

![Pipeline data dan metadata Medallion menuju Atlas](./Bigdata-pipeline-Metadata.jpg)

#### 1.2.1 Alur data (horizontal)

| Urutan | Kotak diagram | Proses di repo | Script / DAG |
|--------|---------------|----------------|--------------|
| 1 | **Source** (×3) | Generator CSV ITERA | `scripts/generate_bronze_data.py` |
| 2 | **Staging** | Upload CSV ke MinIO `staging/` | `staging_to_bronze_pipeline` → task upload |
| 3 | **Columnar table processing** | Profiling + validasi awal | `_profile_csv` / Spark `profile_dataframe` |
| 4 | **Tables → Bronze** | CSV → Iceberg `lakehouse.bronze.*` | `scripts/spark/staging_to_bronze.py` |
| 5 | **Extract → Tables** | Baca Bronze, quality gate | `scripts/spark/bronze_to_silver.py` |
| 6 | **Silver** | Enrichment, business rules | `bronze_silver_metadata_pipeline` |
| 7 | **Transform → Tables** | Star schema 5 dim + 10 fakta | `scripts/spark/silver_to_gold.py` |
| 8 | **Load → Gold** | Iceberg `lakehouse.gold.*` | `silver_to_gold_pipeline` |

#### 1.2.2 Alur metadata paralel (B / S / G → Atlas)

| Repositori logis | Jenis metadata (sesuai diagram) | Registrasi Atlas |
|------------------|--------------------------------|------------------|
| **B** (Bronze) | Raw technical, raw lineage, raw profiling, raw classification (PII, layer) | `register_bronze_metadata.py` |
| **S** (Silver) | Clean, quality, transformation lineage, business, compliance | `register_silver_metadata.py` |
| **G** (Gold) | Business, KPI, AI readiness, consumption, advanced lineage | `register_gold_metadata.py` |
| **Atlas API** | Pencarian Solr, graph JanusGraph/HBase | http://localhost:22100 |
| **Insightera Portal** | Data Catalog + dashboard analitik + monitoring (embed) | http://localhost:13000 |

**UMT:** `scripts/atlas/build_umt.py` — agregasi `technical_json`, `business_json`, `operational_json` per `asset_qualified_name`.

#### 1.2.3 Siklus hidup katalog (16 tahap)

![Siklus hidup aset data catalog](./data-catalog-lifecycle.jpeg)

Padanan portal: `/layers`, `/catalog`, `/glossary`, `/lineage`, `/kpi`, `/metadata-quality` — detail tabel lifecycle ada di implementasi portal (`portal-main/pages/catalog/[qualifiedName].tsx`).

---

### 1.3 Pipeline AQE — Adaptive Query Execution (OFF vs ON)

Diagram khusus AQE (sumber: `pipeline-aqe.png`):

![Pipeline Medallion dengan eksperimen AQE OFF dan ON](./pipeline-aqe.png)

#### 1.3.1 Medallion + titik eksperimen AQE

| Tahap | Proses | Catatan AQE |
|-------|--------|-------------|
| Source → Staging → Bronze | Sama dengan §1.2 (satu kali) | Ingest tidak membandingkan AQE |
| Bronze → **Spark + Adaptive Query Execution** | **Inti eksperimen** | Dua skenario: **OFF** dan **ON** |
| Silver | Transform + quality; warehouse terpisah | `warehouse-aqe-off` / `warehouse-aqe-on` |
| Spark + Query workload | W1–W3 join/agregasi/filter | `scripts/benchmark/run_spark_workloads.py` |
| Silver → Gold | Star schema per konteks AQE | `scripts/spark/silver_to_gold_aqe.py` |
| Gold → Query Engine | Trino W4–W6 + Superset | Katalog `lakehouse_aqe_off` / `lakehouse_aqe_on` |
| Dashboard + Monitoring | Grafana: **AQE Experiment**, **Dashboard Insight** (Forecast · Risk · Opportunity · Anomalies), **MLOps Pipeline** | `metrics/*.json`, port 13001 — panduan [`docs/monitoring-grafana/README.md`](docs/monitoring-grafana/README.md) |

#### 1.3.2 Skenario AQE (kotak di tengah diagram)

| Skenario | Perilaku | Konfigurasi Spark (`conf/spark-defaults.conf` + env) |
|----------|----------|-----------------------------------------------------|
| **AQE OFF** | Static query plan + shuffle partition tetap | `spark.sql.adaptive.enabled=false` |
| **AQE ON** | Runtime re-optimization + adaptive shuffle | `adaptive.enabled=true`, coalesce, skew join, local shuffle reader |

**Tiga optimasi AQE ON (sesuai callout diagram):**

1. **Shuffle partition coalescing** — menggabungkan partisi shuffle kecil setelah stage.  
2. **Dynamic partition pruning** — memangkas partisi Iceberg yang tidak relevan saat runtime.  
3. **Skew join optimization** — menangani skew key (mis. `prodi_id=SD` pada profil data AQE).

#### 1.3.3 Penyimpanan ganda untuk audit

| Lapisan | Schema / path (OFF) | Schema / path (ON) |
|---------|---------------------|----------------------|
| Silver | `lakehouse.silver_aqe_off.*` / `warehouse-aqe-off/` | `lakehouse.silver_aqe_on.*` / `warehouse-aqe-on/` |
| Gold | `lakehouse.gold_aqe_off.*` | `lakehouse.gold_aqe_on.*` |

Implementasi katalog: `scripts/spark/lakehouse_catalog.py` · DAG: `scripts/dags/aqe_full_experiment.py`.

---

### 1.4 Ringkasan integrasi tiga metode

| Metode | Fokus penelitian | Artefak utama |
|--------|------------------|---------------|
| **Metadata** | Governance, kualitas metadata, lineage | Atlas entities, UMT, `metadata_quality_*.json` |
| **AQE** | Performa query & pipeline shuffle | `aqe_comparison_*.json`, Grafana |
| **MLOps** | Prediksi IKU & registrasi model | MLflow runs, `fact_*_mlops`, Metadata MLOps di Atlas, Grafana Dashboard Insight |

**Skenario laporan:** `Metadata-AQE-OFF-MLOps` vs `Metadata-AQE-ON-MLOps` (Gold + query + feature join + training).

---

## 2. Metodologi penelitian

Metodologi mengikuti **tiga fase** (Metadata → AQE → MLOps) dan tiga diagram di §1. Kerangka BAB IV mengikuti template di §4.

1. **Studi literatur dan kerangka kualitas metadata**  
   Meninjau dimensi kualitas metadata (misalnya **DAMA-DMBOK** dan taksonomi **Wang & Strong**: intrinsic, contextual, representational, akses) sebagai landasan untuk menjelaskan completeness, accuracy, timeliness, dan consistency.

2. **Perancangan arsitektur referensi**  
   Menetapkan alur Medallion dan alur metadata (B / S / G) menuju Atlas sesuai *Bigdata-pipeline-Metadata.jpg*, serta pemetaan tahapan siklus katalog sesuai *data-catalog-lifecycle.jpeg*.

3. **Implementasi lingkungan eksperimen**  
   Menyediakan stack kontainer (MinIO, Spark, Hive Metastore, Kafka, ZooKeeper, **HBase**, **Solr**, **Apache Atlas**, Airflow) melalui `docker-compose.yml` dan `start.sh`.

4. **Definisi jenis metadata yang diamati**  
   Memetakan **technical** (skema, tipe, lokasi), **business** (owner, domain, glossary), **operational** (kualitas, SLA pembaruan, tag kepatuhan seperti PII) ke layer Bronze / Silver / Gold.

5. **Ingestion dan enrichment**  
   Menjalankan orkestrasi (DAG) yang mensimulasikan ingestion per layer dan pemanggilan **Atlas API**; mendokumentasikan alur **UMT (Unified Metadata Table)** — tabel/logical view yang menyatukan atribut teknis, bisnis, dan operasional untuk analisis coverage (lihat §4.1.4).

6. **Pengumpulan bukti visual dan metrik**  
   Mengambil **screenshot wajib** UI Atlas (search, detail, lineage), cuplikan graph lineage, serta mengisi tabel evaluasi (§4.1.6) dari pengamatan pada lingkungan yang berjalan.

7. **Analisis dan pembahasan**  
   Menginterpretasikan metrik (kenapa Silver > Bronze, pengaruh enrichment), manfaat lineage, peran Atlas sebagai penghubung layer, kelebihan/keterbatasan, dan implikasi governance (§4.2).

---

## 3. Ringkasan teknologi (stack)

| Komponen | Fungsi dalam penelitian |
|----------|-------------------------|
| **MinIO** | Object storage kompatibel S3 untuk layer Bronze / Silver / Gold. |
| **Apache Spark** | Pemrosesan data dan contoh pembuatan tabel Iceberg. |
| **Hive Metastore** | Metastore tabel; integrasi hook Atlas untuk metadata teknis (jika diaktifkan). |
| **Apache Kafka + ZooKeeper** | Notifikasi perubahan entitas Atlas. |
| **Apache HBase** | Backend penyimpanan graph **JanusGraph** untuk Atlas. |
| **Apache Solr** | Indeks pencarian teks dan discovery di Atlas. |
| **Apache Atlas** | Katalog, klasifikasi, lineage, API metadata. |
| **Apache Airflow** | DAG Metadata, AQE, MLOps (`scripts/dags/*`). |
| **PostgreSQL** | Hive metastore, Airflow, Superset, MLflow. |
| **Trino** | Query engine Gold / katalog AQE OFF·ON. |
| **MLflow** | Model registry (GM: Gold-MLOps). |
| **Superset / Grafana** | Dashboard Insight & monitoring AQE. |

Detail image, port, dan cara menjalankan: lihat **§8** di bawah.

---

## 4. Kerangka Hasil dan Pembahasan

Bagian ini adalah **template** isi BAB IV. Paragraf narasi dan screenshot Anda sisipkan pada bagian yang ditandai. Angka subbab mengikuti kerangka yang Anda berikan.

### 4.1 Hasil

#### 4.1.1 Implementasi arsitektur sistem

**Flow metadata** — jelaskan alur dari sumber → staging/bronze → silver → gold, disertai metadata ingestion / enrichment / BI governance yang mengarah ke Atlas (rujuk Gambar pipeline di §1.1).

**Posisi Atlas** — jelaskan Atlas sebagai API dan penyimpanan metadata terpusat yang menghubungkan repositori logis B, S, G dengan portal discovery.

#### 4.1.2 Implementasi metadata management

Tampilkan metadata yang dihasilkan menurut kategori:

| Kategori | Contoh atribut yang dapat ditampilkan |
|----------|--------------------------------------|
| **Technical** | Skema tabel, nama kolom, tipe data, lokasi (`s3a://…`), format file. |
| **Business** | Owner, domain, deskripsi bisnis, istilah glossary. |
| **Operational** | Tag (PII, sensitivitas), aturan retensi, metrik kualitas, frekuensi refresh. |

**Contoh konkret untuk teks:** schema tabel, owner, tag (PII, domain), lineage antar tabel/pipeline.

#### 4.1.3 Implementasi data lineage

- **Screenshot / graph lineage Atlas (WAJIB):**  
  `![Graph lineage Apache Atlas](./docs/screenshots/atlas-lineage.png)`  
  *(Buat folder `docs/screenshots/` dan simpan file tangkapan layar dari UI Atlas lineage graph.)*

**Bagaimana lineage terbentuk otomatis** — uraikan: hook Hive/Spark (jika digunakan), pesan Kafka `ATLAS_HOOK` / `ATLAS_ENTITIES`, pembuatan proses di Atlas, serta ketergantungan pada definisi job/pipeline yang terdaftar.

#### 4.1.4 Implementasi metadata ingestion & enrichment

**UMT (Unified Metadata Table)** — dalam penelitian ini direkomendasikan sebagai **satu tabel atau view logis** (misalnya hasil agregasi dari bronze/silver/gold) dengan kolom minimal:

| Kolom contoh | Sumber layer | Keterangan |
|--------------|--------------|------------|
| `asset_qualified_name` | Atlas | Kunci ke entitas Atlas. |
| `layer` | Bronze/Silver/Gold | Medallion. |
| `technical_json` | Bronze | Skema, tipe, path. |
| `business_json` | Silver | Owner, glossary, domain. |
| `operational_json` | Silver–Gold | Tag, kualitas, KPI. |
| `last_enriched_at` | Silver | Timeliness. |

**Proses ingestion** — alur dari sumber data/metadata ke Atlas (REST, hook, atau batch DAG).

**Enrichment di Silver** — klasifikasi, glossary, business metadata, dan persiapan lineage transformasi.

#### 4.1.5 Implementasi data catalog portal

**Fitur yang harus dibahas:**

| Fitur | Deskripsi singkat |
|-------|-------------------|
| Search dataset | Pencarian full-text / filter tipe entitas (didukung Solr + Atlas). |
| Dataset detail | Halaman properti teknis dan bisnis. |
| Lineage view | Graph asal–tujuan transformasi. |
| Metadata display | Tab/teks deskripsi, tag, klasifikasi. |

**Struktur halaman (contoh untuk teks):**

1. Header / navigasi global  
2. Kotak pencarian dan filter  
3. Daftar hasil (kartu atau tabel)  
4. Halaman detail aset (metadata + tab lineage)  
5. (Opsional) Tautan ke glossary atau kebijakan

**Screenshot UI (WAJIB):**  
- `docs/screenshots/atlas-search.png` — pencarian dataset.  
- `docs/screenshots/atlas-detail.png` — detail aset.  
- `docs/screenshots/atlas-lineage-ui.png` — tampilan lineage.

#### 4.1.6 Hasil evaluasi metadata quality

Isi tabel berikut dari **pengamatan** pada lingkungan nyata (skala misalnya 0–100% atau skor 1–5). Nilai di bawah hanya **contoh format**; ganti dengan data Anda.

**Tabel — kualitas metadata per layer**

| Layer | Completeness | Accuracy | Timeliness | Consistency |
|-------|----------------|----------|------------|-------------|
| Bronze | *diisi* | *diisi* | *diisi* | *diisi* |
| Silver | *diisi* | *diisi* | *diisi* | *diisi* |
| Gold | *diisi* | *diisi* | *diisi* | *diisi* |

**Tabel — metadata coverage (contoh dimensi)**

| Dimensi / aset | Bronze | Silver | Gold |
|----------------|--------|--------|------|
| Skema terdokumentasi | *%* | *%* | *%* |
| Owner / steward | *%* | *%* | *%* |
| Glossary term | *%* | *%* | *%* |
| Klasifikasi (PII, dll.) | *%* | *%* | *%* |

**Tabel — lineage completeness**

| Ruang lingkup | % entitas dengan lineage keluar | % entitas dengan lineage masuk | Catatan |
|-----------------|-----------------------------------|----------------------------------|---------|
| Bronze | *diisi* | *diisi* | *diisi* |
| Silver | *diisi* | *diisi* | *diisi* |
| Gold | *diisi* | *diisi* | *diisi* |

---

### 4.2 Pembahasan

#### 4.2.1 Analisis metadata quality

Bahas secara naratif:

1. **Mengapa completeness meningkat?** — karena enrichment dan validasi di Silver/Gold.  
2. **Mengapa Silver > Bronze?** — Bronze menyimpan raw; Silver menambah aturan bisnis, kualitas, dan konsistensi istilah.  
3. **Pengaruh enrichment** — hubungan dengan dimensi Wang & Strong (representational, contextual) dan prinsip DAMA (documented, trusted metadata).

**Kontribusi utama penelitian (sisipkan di akhir subbab):** misalnya integrasi Medallion–Atlas–Solr/HBase pada satu stack reproduksibel, atau kerangka UMT + metrik coverage yang Anda usulkan.

#### 4.2.2 Analisis data lineage

Bahas **manfaat lineage**: transparansi alur data, debugging akar masalah dampak, audit. Jelaskan **bagaimana Atlas membantu** (model proses/entitas, graph, notifikasi).

**Kontribusi utama:** jelas sebutkan apa yang baru dibanding praktik manual atau katalog tanpa graph terpusat.

#### 4.2.4 Analisis integrasi Atlas dalam Medallion

Bahas bagaimana Atlas:

- **Menghubungkan layer** — qualifiedName, lineage antar tabel/pipeline antar bucket/layer.  
- **Menjadi metadata backbone** — satu API dan satu sumber kebenaran untuk portal katalog.

**Kontribusi utama:** integrasi arsitektur (diagram §1.1) dengan siklus hidup katalog (§1.2) pada implementasi Docker/Airflow Anda.

#### 4.2.5 Kelebihan dan keterbatasan sistem (WAJIB)

| **Kelebihan** | **Keterbatasan** |
|---------------|------------------|
| Metadata terpusat di Atlas | Masih bergantung pada ekosistem Atlas dan konfigurasi hook |
| Lineage otomatis/semi-otomatis saat hook/REST terpasang | Belum real-time penuh jika ingestion bersifat batch |
| Catalog interaktif (search + lineage) | Belum multi-tenant / SSO produksi pada stack contoh ini |
| Reproduksibel via Docker Compose | Sumber daya (RAM/CPU) relatif besar untuk lingkungan lokal |

#### 4.2.6 Implikasi terhadap data governance

Bahas peningkatan **data discovery**, **transparency**, dan **auditability** berkat katalog terpusat dan lineage, serta keterkaitannya dengan kebijakan organisasi (stewardship, klasifikasi PII).

---

## 5. Pengamatan dan metrik evaluasi (ringkas)

Metrik di §4.1.6 diukur melalui kombinasi:

- **Kuesioner/checklist** pada atribut wajib per layer (completeness, consistency).  
- **Sampling** kesesuaian metadata dengan sumber aktual (accuracy).  
- **Stempel waktu** pembaruan di Atlas vs jadwal pipeline (timeliness).  
- **Lineage completeness** — rasio entitas yang memiliki edge masuk/keluar di graph Atlas.

Acuan konsep: **DAMA-DMBOK** (data quality dimensions) dan **Wang & Strong** untuk pembahasan multi-dimensi di §4.2.1.

---

## 6. Arsitektur ringkas (teks)

```
Sumber data → Staging / Bronze → Silver → Gold
                    ↓              ↓        ↓
              metadata B      metadata S  metadata G
                    └────────────┬────────────┘
                                 ↓
                         Atlas API (+ HBase + Solr)
                                 ↓
                      Portal Data Catalog (discovery)
```

*(Diagram detail: §1.1 dan berkas `Bigdata-pipeline-Metadata.jpg`.)*

---

## 7. Layer mapping (Medallion)

| Layer | Storage | Jenis metadata (sesuai diagram pipeline) |
|-------|---------|----------------------------------------|
| **Staging** | `s3a://staging/` | Landing data mentah dari sumber (belum normalisasi Medallion) |
| **Bronze** | `s3a://bronze/` | Raw technical, raw lineage, raw profiling, raw classification |
| **Silver** | `s3a://silver/` | Clean, quality, transformation lineage, business, compliance |
| **Gold** | `s3a://gold/` | Business, KPI, AI, consumption, advanced lineage |

---

## 8. Stack teknologi, menjalankan layanan, dan troubleshooting

### 8.1 Tabel layanan dan port ke host (default)

Port **di mesin host** memakai rentang 15xxx–22xxx agar tidak bentrok dengan MinIO/Postgres/Spark/Airflow umum (mis. 9000, 5432, 8080, 8081). Di dalam jaringan Docker, service tetap memakai port internal (mis. `minio:9000`, `atlas:21000`).

| Service | Image | Port host (default) | Akses UI / klien dari host |
|---------|-------|---------------------|----------------------------|
| Apache Spark Master + Workers | `apache/spark:3.5.1-scala2.12-java17-python3-ubuntu` | **18080** (UI), **17077** (RPC) | http://localhost:18080 |
| **Insightera Portal** | **node:20-alpine (Next.js)** | **13000** | **http://localhost:13000** |
| Apache Airflow | apache/airflow:2.9.1 | **18681** | http://localhost:18681 |
| MinIO | minio/minio:latest | **19000** (S3 API), **19001** (console) | http://localhost:19001 |
| Apache Solr | solr:8.11.2 | **18984** | http://localhost:18984/solr/ — core **vertex_index**, **edge_index**, **fulltext_index** (JanusGraph) dibuat oleh `solr-atlas-init` |
| Apache HBase | harisekhon/hbase:2.1 | **19010** | http://localhost:19010 |
| Apache Atlas | sburn/apache-atlas:2.3.0 | **22100** | http://localhost:22100 |
| Hive Metastore | apache/hive:4.0.0 | **19083** | `thrift://localhost:19083` |
| PostgreSQL | postgres:15-alpine | **15432** | `localhost:15432` |
| Kafka | confluentinc/cp-kafka:7.5.0 | (hanya internal Docker) | `kafka:9092` dari container lain |
| ZooKeeper | confluentinc/cp-zookeeper:7.5.0 | (hanya internal Docker) | `zookeeper:2181` dari container lain |

**Mengubah port:** salin `.env.example` menjadi `.env`, edit nilai `LHMETA_*`, lalu `docker compose up -d` lagi. Variabel yang didukung sama dengan komentar di bagian atas `docker-compose.yml`.

**Melanjutkan stack setelah salah satu service gagal (mis. Spark pull):** dari folder yang sama dengan `docker-compose.yml`:

```bash
docker compose pull spark-master spark-worker-1 spark-worker-2
docker compose up -d spark-master spark-worker-1 spark-worker-2
```

Lalu naikkan layanan lain (Atlas, Airflow, dll.) dengan perintah manual di **§8.2** di bawah, atau jalankan lagi `./start.sh` (umumnya aman untuk service yang sudah berjalan).

### 8.2 Menjalankan

**Script otomatis**

```bash
chmod +x start.sh
./start.sh
```

**Manual**

```bash
docker compose up -d postgres zookeeper kafka
sleep 15

docker compose up -d hbase solr
sleep 45

docker compose up -d minio && sleep 10
docker compose up -d minio-init

docker compose up -d hive-metastore
sleep 20

docker compose up -d spark-master spark-worker-1 spark-worker-2

docker compose up -d atlas

docker compose up -d airflow-init && sleep 20
docker compose up -d airflow-webserver airflow-scheduler
```

### 8.3 Kredensial

| Service | Username | Password |
|---------|----------|----------|
| MinIO | minioadmin | minioadmin123 |
| Airflow | airflow | airflow |
| Atlas | admin | admin |
| PostgreSQL | admin | admin123 |

### 8.4 Bucket MinIO

| Bucket | Fungsi |
|--------|--------|
| staging | Landing raw dari sumber ke MinIO |
| bronze | Raw ingestion ke layer Medallion |
| silver | Data terkurasi |
| gold | Data siap bisnis |
| warehouse | Penyimpanan tabel Iceberg |
| airflow-logs | Log Airflow |

### 8.5 Contoh Spark + Iceberg

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("LakehouseMetadata") \
    .getOrCreate()

spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")
spark.sql("""
  CREATE TABLE IF NOT EXISTS lakehouse.bronze.raw_metadata (
    id          STRING,
    table_name  STRING,
    column_name STRING,
    data_type   STRING,
    description STRING,
    created_at  TIMESTAMP
  )
  USING iceberg
  LOCATION 's3a://bronze/raw_metadata/'
""")

spark.sql("""
  INSERT INTO lakehouse.bronze.raw_metadata VALUES
  ('1', 'customers', 'email', 'STRING', 'Customer email address', current_timestamp()),
  ('2', 'orders', 'order_id', 'BIGINT', 'Unique order identifier', current_timestamp())
""")

spark.sql("SELECT * FROM lakehouse.bronze.raw_metadata").show()
```

### 8.6 Contoh ingestion Atlas (REST)

```bash
curl -u admin:admin \
  -X POST http://localhost:22100/api/atlas/v2/entity \
  -H "Content-Type: application/json" \
  -d '{
    "entity": {
      "typeName": "hive_table",
      "attributes": {
        "qualifiedName": "bronze.raw_metadata@lakehouse",
        "name": "raw_metadata",
        "description": "Bronze layer raw technical metadata"
      }
    }
  }'
```

### 8.7 Menghentikan stack

```bash
docker compose down
docker compose down -v
```

### 8.8 Persyaratan sistem

- RAM: minimal 8 GB (disarankan 12 GB+)
- CPU: minimal 4 core
- Disk: minimal 15 GB kosong
- Docker Desktop 4.x atau kompatibel

### 8.9 Troubleshooting

```bash
docker compose logs -f atlas
docker compose logs -f hive-metastore
docker compose logs -f airflow-webserver
docker compose ps
docker compose restart atlas
docker compose exec spark-master bash
docker compose exec hive-metastore bash
```

**Kafka — `InconsistentClusterIdException` (cluster ID tidak cocok dengan `meta.properties`)**  
Terjadi jika volume **`kafka-data`** berisi broker lama sementara **ZooKeeper** sudah cluster baru (atau sebaliknya). Data topic Kafka untuk dev ini boleh dihapus.

Container yang berhenti **masih mengunci volume**; hapus container Kafka dulu, baru `docker volume rm`:

```bash
docker volume ls | grep kafka-data
docker compose stop kafka
docker compose rm -f kafka
docker volume rm bigdata-metadata_kafka-data   # ganti dengan output `docker volume ls | grep kafka-data` (bukan teks placeholder NAMA_*)
docker compose up -d kafka
docker compose logs kafka --tail 20
```

Prefiks volume mengikuti **nama folder** proyek Compose (bukan harus `bigdata-metadata`). Jika `docker volume rm` menolak (“in use”), pastikan `docker compose rm -f kafka` sudah jalan dan tidak ada container lain yang memakai volume itu.

Reset berpasangan ZooKeeper + Kafka bila perlu:

```bash
docker volume ls | grep -E 'kafka-data|zookeeper-data'
docker compose stop kafka zookeeper
docker compose rm -f kafka zookeeper
docker volume rm bigdata-metadata_kafka-data bigdata-metadata_zookeeper-data   # ganti dari: docker volume ls | grep -E 'kafka-data|zookeeper-data'
docker compose up -d zookeeper kafka
```

**Solr — `solr-atlas-init` exit 8 (wget / HTTP error)**  
Skrip init memanggil API Solr `CREATE` core; **exit 8** biasanya respons error Solr (mis. konfigurasi core tidak valid). Cek: `docker compose logs solr-atlas-init`. Pastikan repositori berisi **`solr/atlas-config/index_synonyms.txt`** (direferensikan `schema.xml`); bila core setengah jadi, hapus volume dev Solr lalu ulangi init.

**Solr — init exit 1, log: “Solr tidak merespon …”**  
Biasanya healthcheck Solr memakai **GET** `/solr/admin/info/system` (bukan `/admin/ping` — tanpa core, ping sering gagal). `git pull` lalu `docker compose up -d solr` sampai healthy, baru `solr-atlas-init`.

**Volume `in use` saat `docker volume rm …_solr-data`**  
Container **lhmeta-solr** (walau `stop`) masih mereferensikan volume. Hapus container Solr dulu, baru volume:

```bash
docker compose stop solr solr-atlas-init atlas
docker compose rm -f solr solr-atlas-init atlas
docker volume rm bigdata-metadata_solr-data   # nama pasti dari: docker volume ls | grep solr-data
docker compose up -d solr
# tunggu healthy, lalu:
docker compose up -d solr-atlas-init atlas
```

**Atlas — log `Server starting with TLS ? true` / `cert.stores.credential.provider.path`**  
Atlas memilih **SecureEmbeddedServer** tanpa keystore/credential provider → crash sebelum HTTP. Di stack dev kita set **`atlas.enableTLS=false`** di `atlas-conf/atlas-application.properties`. Setelah `git pull`, restart **tanpa** menjalankan ulang init Solr:

```bash
docker compose up -d --force-recreate --no-deps atlas
```

Bila Anda sengaja menjalankan ulang `solr-atlas-init`, skrip di repo sudah menganggap core yang sudah ada sebagai sukses (idempotent).

**Atlas — log JanusGraph `Solr6Index` / `Server error writing document` (bootstrap gagal)**  
Biasanya Solr kehabisan heap atau skema `managed-schema` tidak cocok dengan field dinamis Janus. Di repo: **`SOLR_HEAP=1024m`**, dan **`solrconfig.xml`** memakai **`ClassicIndexSchemaFactory`**. Setelah `git pull`, bersihkan data Solr dev dan buat ulang core, lalu naikkan Atlas.

**Penting:** `docker volume rm …_solr-data` gagal (“in use”) jika container **`lhmeta-solr`** masih ada — wajib **`docker compose rm -f solr`** (bukan hanya `stop`):

```bash
docker compose stop atlas solr solr-atlas-init
docker compose rm -f atlas solr solr-atlas-init
docker volume rm bigdata-metadata_solr-data   # dari: docker volume ls | grep solr-data
docker compose up -d solr
docker compose up -d solr-atlas-init
docker compose up -d atlas
```

Detail error ada di **`docker compose logs solr`** saat waktu yang sama dengan baris error di log Atlas.

**Atlas — log HBase `127.0.0.1:2181` / `Connection refused`**  
`atlas.graph.storage.hbase.zookeeper.quorum` harus berisi **hostname saja** (mis. `hbase`), bukan `hbase:2181`; port pakai **`atlas.graph.storage.hbase.zookeeper.property.clientPort=2181`**. Format `host:2181` sering membuat klien memakai default `localhost:2181` di dalam container.

Image **sburn/apache-atlas** juga memuat **`/apache-atlas/hbase/conf/hbase-site.xml`** di classpath; bawaannya mengarah ke localhost. Repositori ini memasang **`atlas-conf/hbase-site.xml`** ke path itu lewat `docker-compose.yml` — pastikan file tersebut ada setelah `git pull`.

---

## 9. Pipeline Implementasi — Full Medallion Architecture

### 9.1 Pipeline 1: Staging → Bronze

**Script:**
- `scripts/spark/staging_to_bronze.py` — PySpark ETL: CSV → Iceberg tables
- `scripts/atlas/register_bronze_metadata.py` — Atlas: technical metadata + profiling + classification
- `scripts/dags/staging_bronze_pipeline.py` — Airflow DAG

**Metadata yang dicatat ke Atlas (layer B):**
1. **Raw Technical Metadata** — skema tabel, tipe kolom, lokasi S3, format file
2. **Raw Lineage** — staging CSV → bronze Iceberg table
3. **Raw Data Profiling** — row_count, null_count, distinct_count, completeness per kolom
4. **Raw Classification** — `PII`, `Staging_Layer`, `Bronze_Layer`

**Dokumentasi:** [`docs/staging-to-bronze/README.md`](docs/staging-to-bronze/README.md)

---

### 9.2 Pipeline 2: Bronze → Silver

**Script:**
- `scripts/spark/bronze_to_silver.py` — PySpark ETL: cleaning, enrichment, quality checks
- `scripts/atlas/register_silver_metadata.py` — Atlas: quality + business + compliance metadata
- `scripts/dags/bronze_silver_pipeline.py` — Airflow DAG

**Metadata yang dicatat ke Atlas (layer S):**
1. **Clean Metadata** — skema setelah transformasi, tipe enriched
2. **Quality Metadata** — quality_score, status (PASS ≥80%, QUARANTINE 60-79%, REJECT <60%)
3. **Transformation Lineage** — multi-source bronze → silver table
4. **Business Metadata** — owner, IKU relevance, glossary terms, deskripsi bisnis
5. **Compliance Metadata** — PII fields, data classification, retention policy, access restrictions

**Dokumentasi:** [`docs/bronze-to-silver/README.md`](docs/bronze-to-silver/README.md)

---

### 9.3 Pipeline 3: Silver → Gold (Star Schema)

**Script:**
- `scripts/spark/silver_to_gold.py` — PySpark ETL: star schema (5 dimensi + 10 fakta IKU)
- `scripts/atlas/register_gold_metadata.py` — Atlas: KPI + consumption + AI metadata
- `scripts/dags/silver_gold_pipeline.py` — Airflow DAG

**Star Schema:**
- **5 Dimensi:** `dim_waktu`, `dim_prodi`, `dim_dosen`, `dim_mahasiswa`, `dim_topik_penelitian`
- **10 Fakta IKU:** `fact_iku1_lulusan` s.d. `fact_iku8_akreditasi_internasional` + `fact_tata_kelola` + `fact_rekap_iku_institusi`

**Metadata yang dicatat ke Atlas (layer G):**
1. **Business Metadata** — KPI definitions, star schema relationships, ownership
2. **KPI Metadata** — target Renstra per tahun, capaian aktual, status capaian, formula
3. **AI Metadata** — ML readiness, feature store candidates, suggested models
4. **Consumption Metadata** — consumers (Rektor, Wakil Rektor, LP3M, dll), dashboard panel, OLAP role
5. **Advanced Lineage** — full chain staging → bronze → silver → gold (end-to-end)

**Atlas Classifications Gold:**

| Classification | Deskripsi |
|---------------|-----------|
| `Gold_Layer` | Semua tabel di Gold layer |
| `Star_Schema_Dimension` | Tabel dimensi |
| `Star_Schema_Fact` | Tabel fakta |
| `KPI_Metric` | Tabel berisi metrik KPI/IKU |
| `Executive_Dashboard` | Data untuk Dashboard Pimpinan |

**Dokumentasi:** [`docs/silver-to-gold/README.md`](docs/silver-to-gold/README.md) · **Serving & dashboard KPI:** [`docs/gold-to-serving/README.md`](docs/gold-to-serving/README.md)

---

### 9.4 Insightera Portal (Next.js — `portal-main/`)

**Folder:** `portal-main/` — **portal terpadu**: modul **Data Catalog** (Atlas), **Dashboard Analitik** (Superset embed), **Monitoring** (Grafana: Insight, AQE, MLOps). Panduan: [`docs/portal/README.md`](docs/portal/README.md).

**Menjalankan:**
```bash
docker compose up -d portal
# Akses: http://localhost:13000
```

**Modul Data Catalog — halaman & lifecycle (Figure 7-3):**

| Route | Fungsi | Lifecycle Stage |
|-------|--------|-----------------|
| `/` | Overview — statistik entity, layer, classification | 11 (Discovered) |
| `/catalog` | Browse & search datasets dengan filter layer/type | 11 (Discovered) |
| `/catalog/[qualifiedName]` | Detail dataset + **lifecycle tracker, edit, request access, share, export** | 5, 11-13, 16 |
| `/lineage` | Overview lineage seluruh pipeline | 7-8 (Lineage, Graph) |
| `/lineage/[guid]` | Lineage detail per entity (graph + relations) | 7-8, 15 (New Lineage) |
| `/kpi` | KPI Dashboard — 8 IKU + star schema overview | 10 (Published) |
| `/classifications` | Browse classification types | 9 (via API) |
| `/glossary` | Business glossary — **Atlas Glossary API + local terms** | 6 (Glossary Terms) |
| `/quality` | Data quality overview (pass/quarantine/reject) | 9 (via API) |
| `/layers` | Medallion architecture layer browser | 1-2 (Domain, Selection) |
| `/metadata-quality`, `/umt` | Evaluasi metadata & unified metadata table | — |

**Modul Dashboard & Monitoring (embed):**

| Route | Layanan |
|-------|---------|
| `/dashboards` | Hub akses cepat |
| `/dashboards/analitik` | Apache Superset — KPI Gold |
| `/dashboards/insight` | Grafana — Forecast, Risk, Opportunity, Anomalies |
| `/dashboards/monitoring-aqe` | Grafana — eksperimen AQE |
| `/dashboards/monitoring-mlops` | Grafana — pipeline MLOps |

**Fitur lifecycle baru pada halaman detail dataset (`/catalog/[qualifiedName]`):**

| Fitur | Stage Lifecycle | Deskripsi |
|-------|-----------------|-----------|
| Lifecycle Tracker | 1-16 | Visualisasi 16 tahapan lifecycle per aset (Sandbox → Enrichment → Production → Evolution) |
| Edit Metadata | 16 (Update description) | Form edit deskripsi dan owner, push ke Atlas REST API |
| Request Access | 12 (Asset requested) | Modal request akses dengan alasan, kirim ke data steward |
| Share / Export | 13 (Asset shared) | Share via link/email, export metadata JSON |
| Copy Link | 13 (Asset shared) | Salin URL aset ke clipboard |

**API Routes (proxy ke Atlas):**

| Endpoint | Atlas API |
|----------|-----------|
| `/api/atlas/search` | `POST /api/atlas/v2/search/basic` |
| `/api/atlas/entity/[guid]` | `GET /api/atlas/v2/entity/guid/{guid}` |
| `/api/atlas/entity/[guid]/update` | `PUT /api/atlas/v2/entity/guid/{guid}` |
| `/api/atlas/lineage/[guid]` | `GET /api/atlas/v2/lineage/{guid}` |
| `/api/atlas/classifications` | `GET /api/atlas/v2/types/typedefs?type=classification` |
| `/api/atlas/metrics` | `GET /api/atlas/v2/admin/metrics` |
| `/api/atlas/glossary` | `GET/POST /api/atlas/v2/glossary` |
| `/api/atlas/glossary/[guid]/terms` | `GET /api/atlas/v2/glossary/{guid}/terms` |

---

### 9.5 Ringkasan portal & katalog

```
Pipeline Lineage (end-to-end):
  Source CSV → Staging → Bronze (Iceberg) → Silver (Enriched) → Gold (Star Schema)

Atlas Entities:
  Staging:  12 lakehouse_dataset (CSV)
  Bronze:   12 lakehouse_dataset (Iceberg)
  Silver:    6 lakehouse_dataset (Enriched)
  Gold:     15 lakehouse_dataset (5 dim + 10 fact)
  Total:   ~45 entities

Lineage Processes:
  staging → bronze:   12 lakehouse_etl_process
  bronze → silver:     6 lakehouse_etl_process
  silver → gold:     ~13 lakehouse_etl_process
  Total:             ~31 processes

Classifications (11 total):
  PII, Staging_Layer, Bronze_Layer, Silver_Layer, Gold_Layer,
  Quality_Pass, Quality_Quarantine, KPI_Metric,
  Star_Schema_Dimension, Star_Schema_Fact, Executive_Dashboard

Metadata per Layer:
  Bronze: Technical, Lineage, Profiling, Classification
  Silver: Clean, Quality, Transform Lineage, Business, Compliance
  Gold:   Business, KPI, AI, Consumption, Advanced Lineage
```

---

## 10. Eksperimen end-to-end & pencatatan metrik

Panduan operasional menjalankan seluruh pipeline metadata, mengumpulkan JSON metrik ke folder `metrics/` di VM/host, dan mengisi template laporan BAB IV.

| Resource | Keterangan |
|----------|------------|
| [`docs/eksperimen/README.md`](docs/eksperimen/README.md) | Alur fase 0–8, perintah, pemetaan subbab |
| [`docs/eksperimen/templates/`](docs/eksperimen/templates/) | Template pencatatan hasil penelitian |
| [`scripts/benchmark/README.md`](scripts/benchmark/README.md) | Skrip benchmark otomatis |
| [`scripts/dags/metadata_full_experiment.py`](scripts/dags/metadata_full_experiment.py) | DAG Airflow E2E |
| [`metrics/`](metrics/) | Output JSON (volume Docker `./metrics`) |

**Jalankan cepat (tiga metode):**

```bash
python3 scripts/generate_bronze_data.py --mode full
./start.sh
mkdir -p metrics && chmod 1777 metrics

# Fase Metadata
docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment

# Fase AQE (OFF lalu ON — satu DAG)
docker exec lhmeta-airflow-scheduler airflow dags trigger aqe_full_experiment

# Fase MLOps (setelah Gold terisi)
docker exec lhmeta-airflow-scheduler airflow dags trigger mlops_pipeline
```

Artefak: `metrics/experiment_summary_latest.json`, `metrics/aqe_comparison_*.json`, `metrics/mlops_metrics_latest.json`, MLflow http://localhost:15500, Grafana http://localhost:13001, portal http://localhost:13000/metadata-quality.

> Panduan eksperimen: [`docs/eksperimen/README.md`](docs/eksperimen/README.md) · Template: [`docs/eksperimen/templates/`](docs/eksperimen/templates/) · **Grafana:** [`docs/monitoring-grafana/README.md`](docs/monitoring-grafana/README.md)

---

## 11. Berkas pendukung di repositori

| Berkas | Keterangan |
|--------|------------|
| `MLOps-pipeline.png` | Diagram gabungan tiga metode (§1.1) |
| `Bigdata-pipeline-Metadata.jpg` | Diagram pipeline data + metadata (§1.2) |
| `pipeline-aqe.png` | Diagram eksperimen AQE OFF/ON (§1.3) |
| `data-catalog-lifecycle.jpeg` | Siklus hidup aset katalog (§1.2) |
| `docker-compose.yml` | Stack layanan; `solr-atlas-init` membuat core Solr Atlas |
| `solr/atlas-config/` | `schema.xml` / `solrconfig.xml` Atlas 2.3 untuk core JanusGraph |
| `scripts/solr-atlas-init.sh` | Membuat core Solr `vertex_index`, `edge_index`, `fulltext_index` |
| `.env.example` | Contoh override port; salin ke `.env` untuk menyesuaikan VM |
| `atlas-conf/atlas-application.properties` | Konfigurasi Atlas |
| `atlas-conf/hbase-site.xml` | Override ZK HBase untuk klien di container Atlas (service `hbase`) |
| `scripts/dags/metadata_pipeline.py` | DAG orkestrasi metadata per layer |
| `scripts/dags/metadata_full_experiment.py` | DAG eksperimen Metadata E2E |
| `scripts/dags/aqe_full_experiment.py` | DAG eksperimen AQE E2E |
| `scripts/dags/mlops_pipeline.py` | DAG MLOps |
| `scripts/spark/bronze_to_silver_aqe.py` | Bronze→Silver dengan skenario AQE |
| `scripts/mlops/` | Preprocessing, features, train, inference |
| `docs/aqe/README.md` | Ringkasan pipeline AQE |
| `docs/mlops/README.md` | Ringkasan pipeline MLOps |
| `docs/gold-to-serving/README.md` | Star schema, OLAP, granularitas, template dashboard KPI IKU |
| `docs/portal/README.md` | Insightera Portal — katalog + dashboard + monitoring |
| `portal-main/` | Kode Next.js portal |
| `docs/monitoring-grafana/README.md` | Dashboard Grafana Insight + MLOps + AQE |
| `monitoring/grafana/provisioning/dashboards/json/` | Template dashboard (provisioned) |
| `scripts/benchmark/` | Skrip evaluasi kualitas metadata & inventaris Atlas |
| `metrics/` | Folder output metrik eksperimen (di-mount ke Airflow) |
| `scripts/generate_bronze_data.py` | Generator data sintetis ITERA (12 CSV) |
| **Pipeline 1: Staging → Bronze** | |
| `scripts/spark/staging_to_bronze.py` | PySpark ETL CSV → Iceberg |
| `scripts/atlas/register_bronze_metadata.py` | Atlas metadata Bronze |
| `scripts/dags/staging_bronze_pipeline.py` | Airflow DAG Pipeline 1 |
| **Pipeline 2: Bronze → Silver** | |
| `scripts/spark/bronze_to_silver.py` | PySpark ETL cleaning + enrichment |
| `scripts/atlas/register_silver_metadata.py` | Atlas metadata Silver |
| `scripts/dags/bronze_silver_pipeline.py` | Airflow DAG Pipeline 2 |
| **Pipeline 3: Silver → Gold** | |
| `scripts/spark/silver_to_gold.py` | PySpark ETL star schema (5 dim + 10 fact) |
| `scripts/atlas/register_gold_metadata.py` | Atlas metadata Gold (KPI, AI, Consumption) |
| `scripts/dags/silver_gold_pipeline.py` | Airflow DAG Pipeline 3 |
| **Insightera Portal (`portal-main`)** | |
| `portal-main/helpers/atlasApi.ts` | Atlas REST API client (TypeScript) |
| `portal-main/pages/api/atlas/*.ts` | Next.js API routes — 8 proxy endpoints (search, entity, update, lineage, classifications, metrics, glossary, glossary terms) |
| `portal-main/pages/index.tsx` | Dashboard overview |
| `portal-main/pages/catalog/` | Browse & detail datasets + **lifecycle tracker, edit, request access, share, export** |
| `portal-main/pages/lineage/` | Lineage visualization (overview + per-entity graph) |
| `portal-main/pages/kpi/` | KPI Dashboard IKU |
| `portal-main/pages/classifications/` | Classification browser |
| `portal-main/pages/glossary/` | Business glossary — **Atlas Glossary API + local fallback** |
| `portal-main/pages/quality/` | Data quality overview |
| `portal-main/pages/layers/` | Medallion architecture layer browser |

---
