# Template — Virtual Dataset SQL (Trino → Superset)

Salin ke **SQL Lab** Superset, sesuaikan schema (`gold` / `gold_aqe_off` / `gold_aqe_on`), simpan sebagai dataset virtual.

## v_rekap_iku_tahun

```sql
SELECT w.tahun, r.iku_kode, r.iku_nama,
       r.nilai_capaian, r.nilai_target, r.satuan, r.status_capaian
FROM lakehouse.gold.fact_rekap_iku_institusi r
JOIN lakehouse.gold.dim_waktu w ON r.waktu_id = w.waktu_id
ORDER BY w.tahun, r.iku_kode;
```

## v_iku4_per_prodi

```sql
SELECT p.prodi_id, p.nama_prodi, p.nama_jurusan,
       f.total_dosen_tetap, f.dosen_s3, f.dosen_sertifikat_industri,
       f.persen_iku4, f.target_iku, f.capaian_iku
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
ORDER BY f.persen_iku4 DESC;
```

## v_iku_subset_tahun (jika rekap belum ada)

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

## v_capaian_roll_up_jurusan (roll-up Level 1)

```sql
SELECT p.nama_jurusan, w.tahun, AVG(f.persen_iku4) AS avg_iku4
FROM lakehouse.gold.fact_iku4_kualifikasi_dosen f
JOIN lakehouse.gold.dim_prodi p ON f.prodi_id = p.prodi_id
JOIN lakehouse.gold.dim_waktu w ON f.waktu_id = w.waktu_id
GROUP BY p.nama_jurusan, w.tahun
ORDER BY w.tahun, p.nama_jurusan;
```

## Catatan eksekusi

| Query | Durasi (ms) | Baris | Tanggal uji |
|-------|-------------|-------|-------------|
| v_rekap_iku_tahun | | | |
| v_iku4_per_prodi | | | |
