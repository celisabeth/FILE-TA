# Template Pencatatan Eksperimen (BAB III–IV)

Folder ini untuk **mencatat hasil penelitian** (runtime DAG, kualitas metadata, metrik AQE/MLOps, screenshot laporan).  
**Bukan** panduan mengklik Apache Superset.

---

## Bingung dengan dashboard Superset?

| Yang Anda cari | Buka dokumen ini |
|--------------|------------------|
| Layar **New dataset**, **DATABASE / SCHEMA / TABLE**, chart KPI | **[`../../gold-to-serving/panduan-lengkap-dashboard-superset.md`](../../gold-to-serving/panduan-lengkap-dashboard-superset.md)** |
| Checklist panel chart Executive IKU | [`../../gold-to-serving/templates/01-dashboard-executive-iku.md`](../../gold-to-serving/templates/01-dashboard-executive-iku.md) |
| Query SQL untuk dataset Superset | [`../../gold-to-serving/templates/06-virtual-dataset-sql.md`](../../gold-to-serving/templates/06-virtual-dataset-sql.md) |

---

## Cara pakai folder `eksperimen/templates/`

1. Jalankan DAG sesuai [`../README.md`](../README.md) (metadata → AQE → MLOps).
2. Setelah setiap fase, buka file template yang relevan.
3. Isi kolom kosong (angka, tanggal, screenshot).
4. Simpan salinan ke folder run Anda, mis. `experiment-runs/run-2026-05-19/`.

Template **tidak** di-upload ke Superset atau Airflow.

---

## Daftar file (eksperimen saja)

| File | Isi | Kapan diisi |
|------|-----|-------------|
| [01-lingkungan-eksperimen.md](01-lingkungan-eksperimen.md) | Spesifikasi VM, versi image | Awal penelitian |
| [02-dataset.md](02-dataset.md) | Volume staging, profil data | Setelah generate data |
| [03-runtime-pipeline.md](03-runtime-pipeline.md) | Durasi task Medallion | Setelah `metadata_full_experiment` |
| [04-kualitas-metadata.md](04-kualitas-metadata.md) | Skor kualitas Bronze/Silver | Setelah metadata |
| [05-coverage-lineage.md](05-coverage-lineage.md) | Lineage Atlas | Setelah registrasi Atlas |
| [06-screenshot-portal.md](06-screenshot-portal.md) | Daftar file screenshot (portal, **bisa** Superset/Grafana) | Saat dokumentasi BAB IV |
| [07-umt-enrichment.md](07-umt-enrichment.md) | UMT JSON | Setelah `collect_umt` |
| [08-checklist-pembahasan.md](08-checklist-pembahasan.md) | Kerangka narasi §4.2 | Menulis bab hasil |
| [09-perbandingan-aqe.md](09-perbandingan-aqe.md) | Tabel OFF vs ON (metrik) | Setelah `aqe_full_experiment` |
| [10-metrik-mlops.md](10-metrik-mlops.md) | Metrik training/inference | Setelah `mlops_pipeline` |
| [11-skenario-e2e-off-on.md](11-skenario-e2e-off-on.md) | Ringkasan skenario penelitian | Akhir eksperimen |
| [12-distribusi-partisi-skew.md](12-distribusi-partisi-skew.md) | Partisi & skew key Silver | Setelah `measure_aqe_experiment partition-skew` |
| [13-efektivitas-komponen-aqe.md](13-efektivitas-komponen-aqe.md) | DPP, coalesce, skew join | Setelah `measure_aqe_experiment components` |
| [14-perbandingan-format-data.md](14-perbandingan-format-data.md) | Parquet vs ORC vs JSON | Setelah `measure_aqe_experiment format` |
| [15-hasil-layer-silver.md](15-hasil-layer-silver.md) | Ringkasan layer Silver saja | Setelah `silver-summary` + DAG AQE |

Panduan langkah & skrip: [`../pengukuran-aqe-4.1.3-4.1.6.md`](../pengukuran-aqe-4.1.3-4.1.6.md)

---

## Urutan disarankan

```text
01–02 (setup) → metadata DAG → 03,04,05,07 → Superset (gold-to-serving) → AQE DAG → 09
→ pengukuran AQE 12–15 (./scripts/run_aqe_measurements.sh docker)
→ MLOps DAG → 10 → 06 screenshot → 08,11 (penulisan)
```

Panduan operasional DAG: [`../README.md`](../README.md)
