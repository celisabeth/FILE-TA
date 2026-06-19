# Template — Perbandingan AQE OFF vs ON (BAB IV §4.1.2–4.1.4)

Sumber: `metrics/aqe_comparison_*.json`, `metrics/bronze_to_silver_aqe_*.json`, Grafana, Spark UI.

## Identitas run AQE

| Item | Nilai |
|------|-------|
| DAG | `aqe_full_experiment` |
| Tanggal | |
| Dataset | `generate_bronze_data.py --mode full` |

## Pipeline Silver (inti eksperimen)

| Metrik | AQE OFF | AQE ON | Δ / speedup |
|--------|---------|--------|-------------|
| `duration_sec` (bronze_to_silver) | | | % |
| `tables_written` | | | |
| `rows_written` | | | |

## Workload Spark (W1–W3)

| ID | Workload | Durasi OFF (s) | Durasi ON (s) | Speedup % |
|----|----------|----------------|---------------|-----------|
| W1 | Join mahasiswa–dosen | | | |
| W2 | Agregasi prodi | | | |
| W3 | Filter + join | | | |

## Workload Trino Gold (W4–W6)

| ID | Durasi OFF (s) | Durasi ON (s) | Catatan |
|----|----------------|---------------|---------|
| W4 | | | join fact–dim |
| W5 | | | agregasi IKU |
| W6 | | | filter |

## Metrik partisi / plan (opsional)

| Metrik | OFF | ON |
|--------|-----|-----|
| Partisi akhir shuffle | | |
| Shuffle bytes | | |
| Skew terdeteksi | ya/tidak | ya/tidak |

## Screenshot

| No | File | Keterangan |
|----|------|------------|
| 1 | | Spark UI — bronze_to_silver_AQE_OFF |
| 2 | | Spark UI — bronze_to_silver_AQE_ON |
| 3 | | Grafana — Lakehouse AQE Experiment |

## Interpretasi awal

-
