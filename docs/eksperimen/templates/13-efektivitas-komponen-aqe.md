# Template — Efektivitas Komponen AQE (BAB IV §4.1.4)

Sumber: `metrics/aqe_measurement_aqe_components_*.json`

## Profil yang diuji

| Profil | Coalesce | Skew join | DPP | Local shuffle |
|--------|----------|-----------|-----|---------------|
| OFF | | | | |
| ON_FULL | | | | |
| ON_COALESCE_ONLY | | | | |
| ON_SKEW_ONLY | | | | |
| ON_DPP_ONLY | | | | |
| ON_LOCAL_SHUFFLE_ONLY | | | | |

## Durasi workload (detik) — skema `silver_aqe_on`

| Profil | W1 join | W2 agregasi | W3 filter+join |
|--------|---------|-------------|----------------|
| OFF | | | |
| ON_COALESCE_ONLY | | | |
| ON_SKEW_ONLY | | | |
| ON_DPP_ONLY | | | |
| ON_LOCAL_SHUFFLE_ONLY | | | |
| ON_FULL | | | |

## Kontribusi relatif (% penurunan vs OFF)

| Komponen | Workload paling terpengaruh | Δ durasi % |
|----------|---------------------------|------------|
| Shuffle coalescing | W2 | |
| Skew join | W1 | |
| Dynamic partition pruning | W3 | |
| Kombinasi (ON_FULL) | | |

## Pembahasan singkat

### Dynamic partition pruning

### Shuffle partition coalescing

### Skew join optimization

## Screenshot

| No | File | Keterangan |
|----|------|------------|
| 1 | | Spark UI — W1 ON_SKEW_ONLY vs OFF |
