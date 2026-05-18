# Template — Runtime Pipeline (BAB IV §4.1.1) — Insight

## Ringkasan eksekusi

| Item | Nilai |
|------|-------|
| Tanggal run | |
| DAG Metadata | `metadata_full_experiment` |
| DAG AQE | `aqe_full_experiment` |
| DAG MLOps | `mlops_pipeline` |
| Status keseluruhan | Berhasil / Gagal |

## Runtime — Metode Metadata

| Tahap | Task Airflow | Durasi (s) | Status | Sumber JSON |
|-------|--------------|------------|--------|-------------|
| Staging → Bronze | staging_to_bronze | | | `staging_to_bronze_*.json` |
| Bronze → Silver | bronze_to_silver | | | `bronze_to_silver_*.json` |
| Silver → Gold | silver_to_gold | | | `silver_to_gold_*.json` |
| **Subtotal** | | | | `experiment_summary_latest.json` |

## Runtime — Metode AQE

| Tahap | OFF (s) | ON (s) | Sumber |
|-------|---------|--------|--------|
| Bronze → Silver | | | `bronze_to_silver_aqe_OFF_*` / `ON_*` |
| Speedup Silver (%) | — | | `aqe_comparison_*.json` |

## Runtime — Metode MLOps

| Task | Durasi (s) | Status |
|------|------------|--------|
| data_preprocessing | | |
| feature_engineering | | |
| train_models | | |
| inference_batch | | |

## Verifikasi

| Layer / layanan | Cek | Hasil |
|-----------------|-----|-------|
| Bronze/Silver/Gold Atlas | entitas per layer | |
| AQE OFF/ON | `silver_aqe_off` vs `silver_aqe_on` row count | |
| MLflow | run terdaftar | |
| Portal | `/metadata-quality` | |

## Screenshot

| No | File |
|----|------|
| 1 | Airflow — 3 DAG sukses |
| 2 | Grafana AQE (opsional) |
