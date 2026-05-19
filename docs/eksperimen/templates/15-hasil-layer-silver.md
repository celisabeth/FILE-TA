# Template — Hasil Evaluasi Layer Silver (BAB IV §4.1.6)

**Cakupan:** hanya **Silver** (`lakehouse.silver_aqe_off` / `silver_aqe_on`). Gold & Trino dilaporkan terpisah (template 09).

Sumber: `aqe_measurement_silver_layer_summary_*.json`, `bronze_to_silver_aqe_*.json`, `workloads_spark_aqe_*.json`

## Tabel Silver yang dihasilkan pipeline

| Tabel | OFF (baris) | ON (baris) | Quality score |
|-------|-------------|------------|---------------|
| silver_mahasiswa | | | |
| silver_dosen | | | |
| silver_lulusan | | | |
| silver_penelitian_pkm | | | |
| silver_kerjasama_aktif | | | |
| silver_akreditasi_aktif | | | |

## Performa pipeline Bronze → Silver

| Metrik | OFF | ON | Speedup % |
|--------|-----|-----|-----------|
| duration_sec | | | |
| rows_written | | | |

## Workload query Silver (W1–W3)

| ID | OFF (s) | ON (s) | Speedup % |
|----|---------|--------|-----------|
| W1 | | | |
| W2 | | | |
| W3 | | | |

## Skew (ringkasan §4.1.3)

| Tabel | skew_ratio | |
|-------|------------|---|
| silver_mahasiswa | | |

## Kualitas data Silver (rata-rata)

| Metrik | OFF | ON |
|--------|-----|-----|
| silver_completeness % | | |

## Kesimpulan layer Silver

-
