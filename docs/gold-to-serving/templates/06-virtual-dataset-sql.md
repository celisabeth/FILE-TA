# Template 06 — Virtual Dataset SQL (semua query)

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)  
Setiap blok SQL = **satu dataset** di Superset (SQL Lab → Run → Save dataset).

---

## Diagnosa: cek Gold setelah `metadata_full_experiment`

Jalankan **berurutan** di **SQL Lab** (database `Lakehouse Gold (IKU)` / schema `gold`).  
Satu blok per Run — jangan gabung banyak `SELECT` dalam satu Run jika Superset hanya menampilkan hasil terakhir.

### Langkah 1 — Apakah tabel terisi?

```sql
SELECT COUNT(*) AS n_rekap FROM lakehouse.gold.fact_rekap_iku_institusi;
```

```sql
SELECT COUNT(*) AS n_waktu FROM lakehouse.gold.dim_waktu;
```

| `n_rekap` | Arti |
|-----------|------|
| `0` | Rekap belum ditulis — tunggu DAG / cek task `silver_to_gold` di Airflow |
| `~40` (8 IKU × 5 tahun) | Normal — lanjut Langkah 2 |

`n_waktu` biasanya **72** (2020–2025 × 12 bulan).

---

### Langkah 2 — JOIN langsung (bukti utama)

```sql
SELECT COUNT(*) AS n_join
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id;
```

| `n_join` | Arti |
|----------|------|
| **≈ `n_rekap`** (mis. 40) | **Sudah benar** — patch `build_dim_waktu` aktif, lanjut dataset [v_rekap_iku_tahun](#v_rekap_iku_tahun--dataset-v_rekap_iku_tahun) |
| **0** tetapi `n_rekap` > 0 | **`waktu_id` masih tidak selaras** — lihat Langkah 3–4 dan [Join alternatif](#join-alternatif-sementara) |
| **0** dan `n_rekap` = 0 | Data kosong — bukan masalah JOIN |

---

### Langkah 3 — Format `waktu_id` (MIN / MAX)

Jalankan **dua query terpisah**:

```sql
SELECT MIN(waktu_id) AS min_rekap, MAX(waktu_id) AS max_rekap
FROM lakehouse.gold.fact_rekap_iku_institusi;
```

```sql
SELECT MIN(waktu_id) AS min_waktu, MAX(waktu_id) AS max_waktu
FROM lakehouse.gold.dim_waktu;
```

| `min_waktu` / `max_waktu` | Status |
|---------------------------|--------|
| **202001 … 202512** | `dim_waktu` sudah format `tahun×100 + bulan` (patch aktif) |
| **1 … 72** | `dim_waktu` masih versi lama — VM belum pakai kode baru atau DAG belum menulis ulang dimensi |

Fakta/rekap biasanya **202112 … 202512** (Desember per tahun laporan).

---

### Langkah 4 — Orphan `waktu_id` (jangan salah baca)

```sql
SELECT DISTINCT r.waktu_id
FROM lakehouse.gold.fact_rekap_iku_institusi r
LEFT JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
WHERE w.waktu_id IS NULL
LIMIT 20;
```

| Hasil di Superset | Arti |
|-------------------|------|
| **“The query returned no data”** (0 baris) | **Bagus** — tidak ada `waktu_id` di rekap yang tidak punya pasangan di `dim_waktu` |
| Ada baris (mis. `202412`, `202512`, …) | **Buruk** — masih mismatch; pakai [Join alternatif](#join-alternatif-sementara) atau re-run DAG dengan kode patch |

> **Penting:** Query ini **bukan** “apakah rekap ada isinya?”. Kosong di sini **bukan** bukti Airflow gagal. Bukti perbaikan = **`n_join` ≈ `n_rekap`** (Langkah 2).

---

### Langkah 5 — Setelah patch: pastikan Airflow pakai kode baru

Di VM (setelah `git pull` / sync repo):

```bash
# Harus menampilkan baris: waktu_id = tahun * 100 + bulan
docker exec lhmeta-airflow-scheduler grep "waktu_id = tahun" /opt/airflow/scripts/spark/silver_to_gold.py

docker exec lhmeta-airflow-scheduler airflow dags trigger metadata_full_experiment
```

Tunggu task **silver → gold** **success** di UI Airflow, lalu ulangi **Langkah 1–2**.

**AQE** (schema `gold_aqe_off` / `gold_aqe_on`): patch sama di `silver_to_gold_aqe.py` — trigger terpisah:

```bash
docker exec lhmeta-airflow-scheduler airflow dags trigger aqe_full_experiment
```

Ganti `lakehouse.gold` → `gold_aqe_off` atau `gold_aqe_on` pada query di atas.

---

### Ringkasan interpretasi

| `n_rekap` | `n_join` | Query orphan (Langkah 4) | MIN/MAX `dim_waktu` | Tindakan |
|-----------|----------|--------------------------|---------------------|----------|
| 0 | 0 | no data | — | Trigger `metadata_full_experiment` |
| > 0 | ≈ n_rekap | no data | 202xxx | **OK** — pakai SQL [v_rekap_iku_tahun](#v_rekap_iku_tahun--dataset-v_rekap_iku_tahun) |
| > 0 | 0 | ada baris OR no data* | 1…72 | [Join alternatif](#join-alternatif-sementara) + sync kode + re-run DAG |
| > 0 | 0 | no data | 1…72 | *Orphan kosong bisa terjadi jika rekap kosong; andalkan Langkah 3 |

| Gejala lain | Solusi |
|-------------|--------|
| `n_join` > 0 di Trino, 0 baris di Superset chart | Database Superset salah — pilih `Lakehouse Gold (IKU)` |
| Rekap kosong, fakta IKU ada | Query fallback [v_iku_subset_tahun](#v_iku_subset_tahun--dataset-v_iku_subset_tahun) |

---

### Join alternatif (sementara)

Jika **`n_rekap` > 0** tetapi **`n_join` = 0** (VM belum re-run dengan patch):

```sql
SELECT COUNT(*) AS n_join_fix
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w
  ON w.tahun = CAST(r.waktu_id / 100 AS INTEGER)
 AND w.bulan = MOD(r.waktu_id, 100);
```

| `n_join_fix` | Arti |
|--------------|------|
| ≈ `n_rekap` (mis. 40) | Data ada; simpan dataset executive dengan JOIN ini sampai DAG menulis ulang `dim_waktu` |

Dataset executive sementara:

```sql
SELECT w.tahun, r.iku_kode, r.iku_nama,
       r.nilai_capaian, r.nilai_target, r.satuan, r.status_capaian
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w
  ON w.tahun = CAST(r.waktu_id / 100 AS INTEGER)
 AND w.bulan = MOD(r.waktu_id, 100)
ORDER BY w.tahun, r.iku_kode;
```

Setelah `metadata_full_experiment` sukses dengan kode terbaru, **`n_join`** (Langkah 2) harus ≈ 40 dan JOIN `r.waktu_id = w.waktu_id` cukup untuk dataset resmi.

---

## v_rekap_iku_tahun → dataset `v_rekap_iku_tahun`

**Dipakai di:** [01-dashboard-executive-iku.md](01-dashboard-executive-iku.md) chart bar 8 IKU.

```sql
SELECT w.tahun, r.iku_kode, r.iku_nama,
       r.nilai_capaian, r.nilai_target, r.satuan, r.status_capaian
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
ORDER BY w.tahun, r.iku_kode;
```

**Superset:** SQL Lab → Run (>0 baris) → Save dataset → `v_rekap_iku_tahun`.

**Chart:** X-Axis `iku_kode` · Y-Axis **AVG** `nilai_capaian` · Filter `tahun` → [01](01-dashboard-executive-iku.md).

---

## v_iku4_per_prodi → dataset `v_iku4_per_prodi`

**Dipakai di:** [04-dashboard-prodi-drilldown.md](04-dashboard-prodi-drilldown.md).

```sql
SELECT p.prodi_id, p.nama_prodi, p.nama_jurusan,
       f.total_dosen_tetap, f.dosen_s3, f.dosen_sertifikat_industri,
       f.persen_iku4, f.target_iku, f.capaian_iku
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
ORDER BY f.persen_iku4 DESC;
```

**Chart:** X-Axis `nama_prodi` · Y-Axis **AVG** `persen_iku4` · Orientation horizontal → [04](04-dashboard-prodi-drilldown.md).

---

## v_tata_kelola_tahun → dataset `v_tata_kelola_tahun`

**Dipakai di:** [03-dashboard-tata-kelola-sakip.md](03-dashboard-tata-kelola-sakip.md).

```sql
SELECT w.tahun, f.predikat_sakip, f.nilai_sakip,
       f.pagu_total, f.realisasi_total, f.persen_realisasi,
       f.target_kinerja_anggaran
FROM lakehouse.gold.fact_tata_kelola f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
ORDER BY w.tahun;
```

**Chart:** X-Axis `tahun` · Y-Axis **AVG** `persen_realisasi` → [03](03-dashboard-tata-kelola-sakip.md).

---

## v_iku_subset_tahun → dataset `v_iku_subset_tahun`

**Dipakai jika** `fact_rekap_iku_institusi` kosong — chart IKU sementara dari fakta per indikator.

```sql
SELECT w.tahun, 'IKU-4' AS iku_kode, AVG(f.persen_iku4) AS nilai_capaian, AVG(f.target_iku) AS nilai_target
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
GROUP BY w.tahun
UNION ALL
SELECT w.tahun, 'IKU-6', AVG(f.persen_iku6), AVG(f.target_iku)
FROM lakehouse.gold.fact_iku6_kerjasama_prodi f
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
GROUP BY w.tahun
ORDER BY tahun, iku_kode;
```

**Chart (fallback):** X-Axis `iku_kode` · Y-Axis **AVG** `nilai_capaian` · Filter `tahun`.

---

## v_capaian_roll_up_jurusan → dataset `v_capaian_roll_up_jurusan`

**Dipakai di:** [04-dashboard-prodi-drilldown.md](04-dashboard-prodi-drilldown.md) roll-up jurusan.

```sql
SELECT p.nama_jurusan, w.tahun, AVG(f.persen_iku4) AS avg_iku4
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
GROUP BY p.nama_jurusan, w.tahun
ORDER BY w.tahun, p.nama_jurusan;
```

**Chart:** X-Axis `nama_jurusan` · Y-Axis **AVG** `avg_iku4` · Filter `tahun` → [04](04-dashboard-prodi-drilldown.md).

---

## Prefix AQE OFF / ON

| Koneksi Superset | Ganti `lakehouse.gold` menjadi |
|------------------|-------------------------------|
| Lakehouse AQE OFF | `gold_aqe_off` |
| Lakehouse AQE ON | `gold_aqe_on` |

Lihat [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md).

---

## Tabel: Query → Dataset → Chart → Template

| Query / dataset | Template | Chart type | X-Axis | Y-Axis (Metrics) |
|-----------------|----------|------------|--------|------------------|
| `v_rekap_iku_tahun` | 01 Executive | Bar vertikal | `iku_kode` | AVG `nilai_capaian` |
| `v_tata_kelola_tahun` | 03 SAKIP | Line | `tahun` | AVG `persen_realisasi` |
| `v_tata_kelola_tahun` | 03 SAKIP | Bar grouped | `tahun` | SUM `pagu_total`, SUM `realisasi_total` |
| `v_iku4_per_prodi` | 04 Prodi | Bar horizontal | `nama_prodi` | AVG `persen_iku4` |
| `v_capaian_roll_up_jurusan` | 04 Prodi | Bar vertikal | `nama_jurusan` | AVG `avg_iku4` |
| `v_iku_subset_tahun` | 01 (fallback) | Bar vertikal | `iku_kode` | AVG `nilai_capaian` |
| Per `fact_ikuN_*` | 02 per IKU | Bar horizontal | `nama_prodi` / `nama_jurusan` | AVG kolom % IKU |

Detail langkah Explore: file template masing-masing + [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md).

---

## Catatan eksekusi

| Query | Baris | Tanggal |
|-------|-------|---------|
| v_rekap_iku_tahun | | |
| v_iku4_per_prodi | | |
