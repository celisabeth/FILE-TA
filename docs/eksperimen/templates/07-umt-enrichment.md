# Template — UMT & Enrichment (BAB IV §4.1.4)

Dari `metrics/umt_latest.json`.

## Ringkasan UMT

| Item | Nilai |
|------|-------|
| generated_at | |
| approximate_count (baris) | |
| Layer terbanyak | |

## Contoh baris UMT (3 aset)

| asset_qualified_name | layer | last_enriched_at | business (ringkas) |
|----------------------|-------|------------------|-------------------|
| | bronze | | |
| | silver | | |
| | gold | | |

## Tahapan enrichment (siklus katalog)

| Tahap lifecycle | Padanan di run ini | Bukti |
|-----------------|-------------------|-------|
| Raw / Bronze technical | staging_to_bronze + register_bronze | |
| Silver enrichment | bronze_to_silver + register_silver | |
| Gold publish | silver_to_gold + register_gold | |
