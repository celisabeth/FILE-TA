# Panduan Koneksi Trino → Apache Superset (Gold → Serving)

Langkah operasional menghubungkan **star schema Gold** di Iceberg ke **Superset** untuk dashboard KPI IKU. Untuk konsep arsitektur (kapan Superset vs Grafana, AQE OFF/ON), lihat [`arsitektur-dashboard-serving.md`](arsitektur-dashboard-serving.md).

**Prasyarat:** stack Insight jalan (`./start.sh` atau `docker compose up -d`), **15 tabel Bronze** + **15 tabel Gold** terisi (`SHOW TABLES FROM lakehouse.bronze` / `lakehouse.gold`).

| Service | URL default | Port |
|---------|-------------|------|
| Trino | http://localhost:18088 | 18088 |
| Superset | http://localhost:18089 | 18089 |
| Portal embed | http://localhost:13000/dashboards | 13000 |

Login Superset: **admin** / **admin**

---

## 1. Ringkasan katalog Trino

| Koneksi Superset (disarankan) | URI SQLAlchemy (dari container Superset) | Schema Gold | Peran |
|------------------------------|------------------------------------------|-------------|--------|
| **Lakehouse utama** | `trino://admin@trino:8080/lakehouse` | `gold` | KPI operasional & governance |
| **AQE OFF (audit)** | `trino://admin@trino:8080/lakehouse_aqe_off` | `gold_aqe_off` | Salinan hasil pipeline AQE OFF |
| **AQE ON (audit)** | `trino://admin@trino:8080/lakehouse_aqe_on` | `gold_aqe_on` | Salinan hasil pipeline AQE ON |

> Satu katalog `lakehouse` juga bisa melihat `gold_aqe_off` / `gold_aqe_on` (semua schema di metastore). Untuk penelitian BAB IV, **dua koneksi terpisah** memudahkan default schema dan mencegah salah tulis schema.

Dari **host** (laptop), ganti host: `trino://admin@localhost:18088/lakehouse`

File katalog: [`../../trino/etc/catalog/`](../../trino/etc/catalog/)

---

## 2. Verifikasi Trino sebelum Superset

```bash
# Tabel Gold utama
docker exec lhmeta-trino trino --execute "SHOW TABLES FROM lakehouse.gold"

# Salinan audit AQE (setelah aqe_full_experiment)
docker exec lhmeta-trino trino --execute "SHOW TABLES FROM lakehouse.gold_aqe_off"
docker exec lhmeta-trino trino --execute "SHOW TABLES FROM lakehouse.gold_aqe_on"

# Sample KPI
docker exec lhmeta-trino trino --execute \
  "SELECT iku_kode, nilai_capaian, nilai_target FROM lakehouse.gold.fact_rekap_iku_institusi LIMIT 5"
```

Jika schema kosong → jalankan DAG `metadata_full_experiment` atau `aqe_full_experiment` (lihat [`../eksperimen/README.md`](../eksperimen/README.md)).

---

## 3. Menambah koneksi database di Superset

### 3.1 Koneksi utama — `lakehouse.gold`

1. Buka http://localhost:18089 → login **admin** / **admin**
2. **Settings** (ikon gear) → **Database connections** → **+ Database**
3. Pilih **Trino**
4. **SQLAlchemy URI** (jalankan dari jaringan Docker):

   ```
   trino://admin@trino:8080/lakehouse
   ```

5. **Display name:** `Lakehouse Gold (IKU)`
6. **Test connection** → harus sukses
7. **Connect**

**Opsi lanjutan (disarankan):**

| Field | Nilai |
|-------|--------|
| Allow CREATE TABLE AS | OFF (read-only BI) |
| Allow DML | OFF |
| Expose in SQL Lab | ON |

### 3.2 Koneksi audit AQE OFF

URI:

```
trino://admin@trino:8080/lakehouse_aqe_off
```

**Display name:** `Lakehouse AQE OFF`

Default schema di SQL Lab: `gold_aqe_off` (tabel sama seperti `lakehouse.gold`, prefix schema berbeda).

### 3.3 Koneksi audit AQE ON

URI:

```
trino://admin@trino:8080/lakehouse_aqe_on
```

**Display name:** `Lakehouse AQE ON`

---

## 4. Membuat dataset fisik

Untuk setiap koneksi, buat dataset dari tabel (bukan hanya virtual SQL):

| Dataset | Tabel penuh (koneksi utama) | Tabel penuh (AQE OFF) | Tabel penuh (AQE ON) |
|---------|----------------------------|----------------------|----------------------|
| dim_waktu | `lakehouse.gold.dim_waktu` | `gold_aqe_off.dim_waktu` | `gold_aqe_on.dim_waktu` |
| dim_prodi | `lakehouse.gold.dim_prodi` | `gold_aqe_off.dim_prodi` | `gold_aqe_on.dim_prodi` |
| fact_rekap_iku_institusi | `lakehouse.gold.fact_rekap_iku_institusi` | `gold_aqe_off.fact_rekap_iku_institusi` | `gold_aqe_on.fact_rekap_iku_institusi` |
| fact_iku4_kualifikasi_dosen | `lakehouse.gold.fact_iku4_kualifikasi_dosen` | … | … |
| fact_tata_kelola | `lakehouse.gold.fact_tata_kelola` | … | … |

**Bronze (opsional — populasi / governance, bukan star schema):** `lakehouse.bronze.raw_fakultas`, `raw_organisasi_itera`, `raw_tendik`, `raw_mahasiswa`, … (15 tabel).

**Langkah UI:** **Data** → **Datasets** → **+ Dataset** → pilih database → pilih schema → pilih tabel → **Add**.

Virtual dataset (SQL): salin dari [`templates/06-virtual-dataset-sql.md`](templates/06-virtual-dataset-sql.md) dan ganti prefix schema (`gold` → `gold_aqe_off` / `gold_aqe_on`).

---

## 5. Membuat dashboard & embed di portal

### 5.1 Dashboard KPI utama (wajib)

Ikuti template [`templates/01-dashboard-executive-iku.md`](templates/01-dashboard-executive-iku.md) pada koneksi **Lakehouse Gold (IKU)**.

Setelah dashboard tersimpan, catat **ID numerik** atau **slug** dari URL Superset:

```
http://localhost:18089/superset/dashboard/12/?standalone=1
                                      ^^
```

Di portal Insightera: **Dashboard Analitik** → **URL Embed** → isi:

```
http://<IP-VM>:18089/superset/dashboard/12/?standalone=1
```

### 5.2 Dashboard KPI AQE OFF / ON (opsional — penelitian)

Duplikasi layout Executive IKU untuk masing-masing koneksi audit. Template: [`templates/07-dashboard-kpi-aqe-off-on.md`](templates/07-dashboard-kpi-aqe-off-on.md).

Portal menyediakan halaman embed terpisah:

| Halaman portal | Katalog Trino | Schema Gold |
|----------------|---------------|-------------|
| `/dashboards/kpi-aqe-off` | `lakehouse_aqe_off` | `gold_aqe_off` |
| `/dashboards/kpi-aqe-on` | `lakehouse_aqe_on` | `gold_aqe_on` |

**Bukan** menggantikan Monitoring AQE di Grafana — itu untuk **metrik performa pipeline** (durasi, speedup), bukan chart KPI Renstra.

---

## 6. Troubleshooting koneksi

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| `Connection refused` ke Trino | Container Trino mati | `docker compose up -d trino` |
| `Catalog lakehouse_aqe_off not found` | File katalog belum ter-mount | Cek `trino/etc/catalog/*.properties`, restart Trino |
| `Schema gold_aqe_off does not exist` | DAG AQE belum jalan | `airflow dags trigger aqe_full_experiment` |
| Chart kosong | Filter tahun / `waktu_id` salah | Preview dataset di Superset |
| `% IKU aneh setelah agregasi` | SUM pada kolom persen | Pakai **AVG** atau hitung ulang dari count |
| Embed portal blank | X-Frame / login | Buka URL embed di tab baru; login Superset sekali |
| URI `localhost` dari VM remote | Host salah | Pakai IP VM: `103.174.114.177:18088` |
| `Column 'record_count' cannot be resolved` | Metrik/partisi Iceberg di chart, bukan kolom | Hapus `record_count` dari chart; pakai `COUNT(*)` — [panduan §11.1](panduan-lengkap-dashboard-superset.md#111-error-record_count--file_count-superset--trino) |

**Uji URI dari container Superset:**

```bash
docker exec lhmeta-superset python -c "
from sqlalchemy import create_engine
e = create_engine('trino://admin@trino:8080/lakehouse')
with e.connect() as c:
    print(c.execute('SELECT COUNT(*) FROM gold.fact_rekap_iku_institusi').scalar())
"
```

*(Sesuaikan nama container jika berbeda: `docker ps | grep superset`)*

---

## 7. Checklist

- [ ] Trino: `lakehouse.gold` berisi 5 dim + 10 fact
- [ ] Superset: 3 koneksi (utama + AQE OFF + AQE ON) — atau minimal koneksi utama
- [ ] Dataset `fact_rekap_iku_institusi` + dimensi terhubung
- [ ] Dashboard Executive IKU + URL embed di portal
- [ ] (Opsional) Dashboard duplikat OFF/ON + embed `/dashboards/kpi-aqe-off` & `kpi-aqe-on`
- [ ] Grafana Monitoring AQE untuk metrik `metrics/aqe_comparison_*.json` — terpisah dari Superset

**Terkaait:** [`README.md`](README.md) · [`arsitektur-dashboard-serving.md`](arsitektur-dashboard-serving.md) · [`../monitoring-grafana/README.md`](../monitoring-grafana/README.md)
