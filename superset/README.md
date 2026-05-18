# Superset (Lakehouse Insight)

## Build & jalankan

```bash
cd ~/Bigdata-insightera   # root repo

# Pastikan config pendek (~11 baris), BUKAN versi lama dengan _patch_trino_...
wc -l superset/superset_config.py    # harus ~11
grep -c patch_trino superset/superset_config.py || true   # harus 0 di superset_config.py

docker compose build --no-cache superset superset-init
docker compose run --rm superset-init
docker compose up -d superset
```

Log build harus ada: `patched /app/superset/db_engine_specs/trino.py`

UI: http://localhost:18089 (admin / admin)

## Patch Iceberg

Bug Superset #26449 (`record_count cannot be resolved`) diperbaiki di **build time** via `patch_trino_iceberg.py` — **bukan** di `superset_config.py`.
