# Pengukuran Eksperimen AQE — §4.1.3 s.d. §4.1.6 (Layer Silver)

Panduan operasional untuk subbab penelitian **Adaptive Query Execution** yang belum tercakup penuh di template lama. **Cakupan implementasi repo:** pengukuran utama pada **layer Silver** (`lakehouse.silver_aqe_off` / `silver_aqe_on`); Gold/Trino (W4–W6) tetap untuk perbandingan serving terpisah.

| Subbab | Topik | Skrip / artefak |
|--------|--------|-----------------|
| **§4.1.3** | Distribusi partisi & data skew | `measure_aqe_experiment.py partition-skew` |
| **§4.1.4** | Efektivitas komponen AQE (DPP, coalesce, skew join) | `measure_aqe_experiment.py components` |
| **§4.1.5** | Perbandingan format data | `measure_aqe_experiment.py format` |
| **§4.1.6** | Hasil per layer (**Silver saja**) | `measure_aqe_experiment.py silver-summary` |

Template isian laporan: [`templates/12-distribusi-partisi-skew.md`](templates/12-distribusi-partisi-skew.md) … [`15-hasil-layer-silver.md`](templates/15-hasil-layer-silver.md).

---

## 0. Prasyarat

```bash
cd /path/to/Data-Lakehouse-Insight
./start.sh
mkdir -p metrics && chmod 1777 metrics

# Data dengan skew (disarankan untuk §4.1.3)
./scripts/generate_data.sh full aqe

# Pipeline Silver OFF + ON
docker exec lhmeta-airflow-scheduler airflow dags trigger aqe_full_experiment
# tunggu sukses: bronze_to_silver_off/on, spark_workloads_*, silver_to_gold_* (opsional untuk Gold)
```

Verifikasi tabel Silver:

```bash
docker exec lhmeta-spark-master spark-sql -e "SHOW TABLES IN lakehouse.silver_aqe_on"
```

---

## 1. §4.1.3 — Distribusi partisi & data skew

**Tujuan:** mengukur ketimpangan key join (`prodi_id`) dan konteks partisi shuffle.

**Jalankan:**

```bash
./scripts/run_aqe_measurements.sh docker partition-skew
# atau satu perintah:
docker exec lhmeta-airflow-scheduler python \
  /opt/airflow/scripts/benchmark/measure_aqe_experiment.py partition-skew --aqe-scenario ON
```

**Output:** `metrics/aqe_measurement_partition_skew_*.json`

| Field | Arti |
|-------|------|
| `skew_ratio_max_over_mean` | max(count per prodi) / rata-rata; > 3 = skew kuat |
| `top_key_share_pct` | % baris pada prodi terbesar |
| `spark_shuffle_partitions_setting` | `spark.sql.shuffle.partitions` |
| `top_keys` | 10 prodi teratas |

**Isian template:** [`templates/12-distribusi-partisi-skew.md`](templates/12-distribusi-partisi-skew.md)

**Bukti tambahan (opsional):** Spark UI → stage `silver_mahasiswa` / workload W1 → skewed partition highlight saat AQE ON.

---

## 2. §4.1.4 — Efektivitas komponen AQE

**Komponen yang diuji** (profil di `scripts/spark/aqe_component_config.py`):

| Profil | `adaptive` | Coalesce | Skew join | DPP | Local shuffle |
|--------|------------|----------|-----------|-----|---------------|
| `OFF` | false | false | false | false | false |
| `ON_FULL` | true | true | true | true | true |
| `ON_COALESCE_ONLY` | true | true | false | false | false |
| `ON_SKEW_ONLY` | true | false | true | false | false |
| `ON_DPP_ONLY` | false | false | false | true | false |
| `ON_LOCAL_SHUFFLE_ONLY` | true | false | false | false | true |

**Workload pengukur:** W1 (join), W2 (agregasi), W3 (filter+join) pada schema `silver_aqe_on`.

**Jalankan:**

```bash
docker exec lhmeta-airflow-scheduler python \
  /opt/airflow/scripts/benchmark/measure_aqe_experiment.py components \
  --aqe-scenario ON \
  --profiles OFF,ON_FULL,ON_COALESCE_ONLY,ON_SKEW_ONLY,ON_DPP_ONLY,ON_LOCAL_SHUFFLE_ONLY
```

**Output:** `metrics/aqe_measurement_aqe_components_*.json`

**Analisis disarankan:**

- Bandingkan `duration_sec` W1: `ON_SKEW_ONLY` vs `OFF` (skew join).
- Bandingkan W2: `ON_COALESCE_ONLY` vs `OFF` (shuffle coalescing).
- Bandingkan W3: `ON_DPP_ONLY` vs `OFF` (dynamic partition pruning ke Iceberg).
- `ON_FULL` vs `OFF` = efek gabungan.

**Template:** [`templates/13-efektivitas-komponen-aqe.md`](templates/13-efektivitas-komponen-aqe.md)

---

## 3. §4.1.5 — Perbandingan format data

**Tujuan:** membandingkan **Parquet vs ORC vs JSON** (write/read + ukuran) pada sampel `silver_mahasiswa`. Produksi memakai **Iceberg/Parquet**; subbab ini isolasi format serialisasi.

```bash
docker exec lhmeta-airflow-scheduler python \
  /opt/airflow/scripts/benchmark/measure_aqe_experiment.py format \
  --aqe-scenario ON --sample-rows 50000
```

**Output:** `metrics/aqe_measurement_format_comparison_*.json` + folder `metrics/format_benchmark/`.

**Template:** [`templates/14-perbandingan-format-data.md`](templates/14-perbandingan-format-data.md)

---

## 4. §4.1.6 — Hasil berdasarkan layer (Silver saja)

**Yang diukur di repo untuk Silver:**

| Aspek | Sumber |
|--------|--------|
| Durasi pipeline Bronze→Silver | `bronze_to_silver_aqe_{OFF\|ON}_*.json` |
| Kualitas / profiling kolom | field `tables.*` dalam file pipeline |
| Workload W1–W3 | `workloads_spark_aqe_{OFF\|ON}_*.json` |
| Skew & partisi | `aqe_measurement_partition_skew_*.json` |
| Komponen AQE | `aqe_measurement_aqe_components_*.json` |

**Tidak masuk §4.1.6 Silver:** Gold star schema, Trino W4–W6 (laporkan di subbab terpisah / template 09).

```bash
docker exec lhmeta-airflow-scheduler python \
  /opt/airflow/scripts/benchmark/measure_aqe_experiment.py silver-summary --aqe-scenario ON
```

**Template:** [`templates/15-hasil-layer-silver.md`](templates/15-hasil-layer-silver.md)

---

## 5. Jalankan semua pengukuran

```bash
chmod +x scripts/run_aqe_measurements.sh
./scripts/run_aqe_measurements.sh docker
```

Atau host lokal (Spark dapat dijangkau):

```bash
export PYTHONPATH=scripts INSIGHT_METRICS_DIR=metrics
./scripts/run_aqe_measurements.sh all
```

---

## 6. Integrasi Grafana & perbandingan OFF/ON

| Metrik | Grafana / Prometheus |
|--------|----------------------|
| Durasi pipeline & workload | Dashboard **Lakehouse AQE Experiment** |
| Komponen / skew / format | JSON di `metrics/` (belum diekspor ke Prometheus) |

Agregasi OFF vs ON (sudah ada):

```bash
PYTHONPATH=scripts python3 scripts/benchmark/compare_aqe_runs.py --markdown
```

---

## 7. Pemetaan ke skripsi

| Pertanyaan penelitian | Bukti |
|----------------------|--------|
| Apakah data skew mempengaruhi performa? | §4.1.3 `skew_ratio` + profil `generate_data.sh full aqe` |
| Komponen AQE mana paling berkontribusi? | §4.1.4 tabel durasi per profil × W1–W3 |
| Format storage terbaik untuk throughput? | §4.1.5 `size_mb`, `write/read_duration_sec` |
| Bagaimana kualitas & performa Silver OFF vs ON? | §4.1.6 + `aqe_comparison_*.json` |
