# Template — Dashboard per Indikator IKU (IKU-1 … IKU-8)

Isi satu blok per IKU yang dianalisis mendalam.

---

## IKU-1 — Lulusan bekerja / studi / wirausaha

| Item | Nilai |
|------|-------|
| Tabel fakta | `fact_iku1_lulusan` |
| Dimensi join | `dim_prodi`, `dim_waktu` |
| Granularitas fakta | Prodi × tahun (akhir tahun) |

| Prodi | Total lulusan | % terserap | Target | Capaian |
|-------|---------------|------------|--------|---------|
| | | | | |

**Visualisasi:** bar horizontal `nama_prodi` × `persen_terserap`

---

## IKU-2 — MBKM / prestasi nasional

| Tabel fakta | `fact_iku2_mbkm` |
|-------------|------------------|
| Metrik utama | `persen_iku2`, `mahasiswa_memenuhi_iku2` |

| Prodi | % IKU-2 | Target | Status |
|-------|---------|--------|--------|
| | | | |

---

## IKU-3 — Dosen tridarma luar kampus

| Tabel fakta | `fact_iku3_dosen_tridarma` |
| Metrik | `persen_iku3`, `dosen_memenuhi_iku3` |

---

## IKU-4 — Kualifikasi dosen (S3 / sertifikat / praktisi)

| Tabel fakta | `fact_iku4_kualifikasi_dosen` |
| Metrik | `persen_iku4`, `dosen_s3`, `dosen_sertifikat_industri` |

| Prodi | Total dosen | S3 | Sertifikat | % IKU-4 |
|-------|-------------|-----|------------|---------|
| | | | | |

---

## IKU-5 — Penelitian rekognisi internasional (per dosen)

| Tabel fakta | `fact_iku5_penelitian_pkm` |
| Granularitas | **Jurusan** (`jurusan_id`), bukan prodi |
| Metrik | `rasio_per_dosen`, `capaian_iku` |

| Jurusan | Total dosen | Output eligible | Rasio |
|---------|-------------|-----------------|-------|
| | | | |

---

## IKU-6 — Kerjasama prodi dengan mitra

| Tabel fakta | `fact_iku6_kerjasama_prodi` |
| Granularitas | **Institusi** (tanpa `prodi_id`) |
| Metrik | `persen_iku6`, `prodi_berkerjasama` / `total_prodi_s1` |

---

## IKU-7 — Metode pembelajaran inovatif

| Tabel fakta | `fact_iku7_metode_pembelajaran` |
| Metrik | `mk_case_method`, `mk_team_based`, `persen_iku7` |

---

## IKU-8 — Akreditasi / sertifikat internasional

| Tabel fakta | `fact_iku8_akreditasi_internasional` |
| Granularitas | Institusi |
| Metrik | `persen_iku8`, `prodi_akreditasi_internasional` |

---

## Ringkasan perbandingan (opsional)

| IKU | Rata capaian institusi | Prodi terbaik | Prodi terendah |
|-----|------------------------|---------------|----------------|
| IKU-4 | | | |

## Screenshot

| IKU | File |
|-----|------|
| IKU-1 | superset-iku1-lulusan.png |
| IKU-4 | superset-iku4-dosen.png |
| … | |
