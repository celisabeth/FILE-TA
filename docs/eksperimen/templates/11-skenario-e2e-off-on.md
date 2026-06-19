# Template — Skenario End-to-End Insight-OFF vs Insight-ON (BAB IV §4.1.5, §4.2.4)

Perbandingan **tiga metode** pada dua konfigurasi AQE (governance + MLOps sama; hanya query engine berbeda).

## Definisi skenario

| Skenario | Metadata (`metadata_full_experiment`) | AQE | MLOps (`mlops_pipeline`) |
|----------|--------------------------------------|-----|---------------------------|
| **Insight-OFF** | ✅ | OFF (`warehouse-aqe-off`) | ✅ |
| **Insight-ON** | ✅ | ON (`warehouse-aqe-on`) | ✅ |

## Tabel perbandingan utama

| Aspek | Insight-OFF | Insight-ON | Sumber bukti |
|-------|-------------|------------|--------------|
| Total DAG metadata (min) | | | Airflow |
| Durasi `aqe_full_experiment` (min) | | | Airflow |
| Silver transform (s) | | | `bronze_to_silver_aqe_*` |
| Speedup Silver (%) | — | | `aqe_comparison_*.json` |
| Trino query avg (s) | | | `workloads_trino_*` |
| Metadata completeness Gold (%) | | | `metadata_quality_latest.json` |
| Lineage coverage Gold (%) | | | `atlas_inventory_latest.json` |
| MLOps training (s) | | | MLflow |
| MLOps inference rows | | | Spark SQL |
| RAM puncak (GB) | | | `docker stats` |

## Dampak AQE pada MLOps (hipotesis)

| Tahap MLOps | OFF | ON | Observasi |
|-------------|-----|-----|-----------|
| Feature join dari Gold | | | |
| Training wall-clock | | | |
| Batch inference | | | |

## Kesimpulan sementara (draft §4.2.4)

| Pertanyaan | Jawaban singkat |
|------------|-----------------|
| Apakah AQE-ON direkomendasikan? | |
| Apakah metadata governance terpengaruh? | |
| Apakah MLOps mendapat manfaat dari AQE? | |

## Rekomendasi operasional

-
