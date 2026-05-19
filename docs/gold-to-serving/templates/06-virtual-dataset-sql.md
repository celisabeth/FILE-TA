# Template 06 — Virtual Dataset SQL (semua query)

**Alur umum:** [00-alur-superset-dataset-chart.md](00-alur-superset-dataset-chart.md)  
Setiap blok SQL = **satu dataset** di Superset (SQL Lab → Run → Save dataset).

---

## Diagnosa: query JOIN mengembalikan 0 baris

Jalankan **berurutan** di SQL Lab:

```sql
-- 1) Apakah tabel ada isinya?
SELECT COUNT(*) AS n FROM lakehouse.gold.fact_rekap_iku_institusi;
SELECT COUNT(*) AS n FROM lakehouse.gold.dim_waktu;

-- 2) Apakah join cocok?
SELECT COUNT(*) AS n_join
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id;

-- 3) Sample waktu_id yang tidak match (jika rekap > 0 tapi join = 0)
SELECT DISTINCT r.waktu_id FROM lakehouse.gold.fact_rekap_iku_institusi r
LEFT JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
WHERE w.waktu_id IS NULL LIMIT 20;
```

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| `fact_rekap` = 0 | Gold rekap belum dibuat | Airflow: `metadata_full_experiment` / task `silver_to_gold` |
| rekap > 0, join = 0 | `waktu_id` tidak ada di `dim_waktu` | Re-run pipeline Gold; cek `build_fact_rekap_iku` |
| join > 0 di Trino, 0 di Superset | Database salah / schema salah | Pastikan database `Lakehouse Gold (IKU)` |

**Alternatif jika rekap kosong tetapi fakta IKU ada** — pakai query **v_iku_subset_tahun** (bawah) untuk chart sementara.

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

**Chart:** Bar horizontal · Dimension `nama_prodi` · Metric **AVG** `persen_iku4`.

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

**Chart:** Line · Dimension `tahun` · Metric **AVG** `persen_realisasi`.

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

---

## Prefix AQE OFF / ON

| Koneksi Superset | Ganti `lakehouse.gold` menjadi |
|------------------|-------------------------------|
| Lakehouse AQE OFF | `gold_aqe_off` |
| Lakehouse AQE ON | `gold_aqe_on` |

Lihat [07-dashboard-kpi-aqe-off-on.md](07-dashboard-kpi-aqe-off-on.md).

---

## Tabel: Query → Dataset → Chart → Template

| Query / dataset | Template | Chart type |
|-----------------|----------|------------|
| `v_rekap_iku_tahun` | 01 Executive | Bar |
| `v_tata_kelola_tahun` | 03 SAKIP | Line |
| `v_iku4_per_prodi` | 04 Prodi | Bar horizontal |
| `v_iku_subset_tahun` | 01 (fallback) | Bar |
| Per `fact_ikuN_*` | 02 per IKU | Bar (satu chart per IKU) |

---

## Catatan eksekusi

| Query | Baris | Tanggal |
|-------|-------|---------|
| v_rekap_iku_tahun | | |
| v_iku4_per_prodi | | |
