# Template — Distribusi Partisi & Data Skew (BAB IV §4.1.3)

Sumber: `metrics/aqe_measurement_partition_skew_*.json`

## Identitas

| Item | Nilai |
|------|-------|
| Tanggal | |
| Skenario AQE data | OFF / ON |
| Dataset | `generate_data.sh full aqe` (skew ke prodi SD) |
| Skema | `lakehouse.silver_aqe_on` |

## Tabel — `silver_mahasiswa` (key: prodi_id)

| Metrik | Nilai |
|--------|-------|
| Total baris | |
| Jumlah prodi (key) | |
| Min / mean / max baris per prodi | |
| **skew_ratio** (max/mean) | |
| **top_key_share_%** | |
| `spark.sql.shuffle.partitions` | |

### Top-5 prodi (baris terbanyak)

| prodi_id | count | % dari total |
|----------|-------|--------------|
| | | |
| | | |

## Tabel — tabel Silver lain

| Tabel | skew_ratio | Catatan |
|-------|------------|---------|
| silver_dosen | | |
| silver_lulusan | | |

## Interpretasi

- Skew ratio > 3: …
- Dampak pada W1 (join mahasiswa–dosen): …
- Screenshot Spark UI (opsional): `docs/screenshots/aqe-skew-w1.png`
