# insightera Portal (`portal-main`)

**Satu pintu masuk** untuk seluruh konsumsi penelitian Data Lakehouse Insight — bukan hanya katalog metadata. Frontend Next.js (template Facit/Bootstrap) di folder [`../../portal-main/`](../../portal-main/), dijalankan sebagai service Docker **`portal`**.

| Area | Path portal | Backend |
|------|-------------|---------|
| **Overview** | `/` | Ringkasan layer & Atlas |
| **Data Catalog** | `/catalog`, `/lineage`, `/glossary`, `/layers`, `/quality`, `/classifications` | Apache Atlas |
| **Metadata & UMT** | `/metadata-quality`, `/umt` | Atlas + skrip benchmark |
| **KPI (built-in)** | `/kpi` | Atlas entities Gold / IKU |
| **Dashboard Analitik** | `/dashboards/analitik` | Apache Superset (embed) |
| **Dashboard Insight** | `/dashboards/insight` | Grafana — Forecast, Risk, Opportunity, Anomalies |
| **Monitoring AQE** | `/dashboards/monitoring-aqe` | Grafana — eksperimen AQE |
| **Monitoring MLOps** | `/dashboards/monitoring-mlops` | Grafana — pipeline MLOps |

---

## 1. Arsitektur portal

```
                    ┌─────────────────────────────────────┐
                    │   insightera Portal (:13000)        │
                    │   portal-main (Next.js)             │
                    └───────────┬─────────────────────────┘
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   ┌─────────────┐      ┌─────────────┐       ┌─────────────┐
   │ Apache Atlas│      │  Superset   │       │   Grafana   │
   │  :21000     │      │  :18089     │       │   :13001    │
   │  (proxy API)│      │  (iframe)   │       │   (iframe)  │
   └─────────────┘      └─────────────┘       └─────────────┘
   Katalog · lineage    KPI OLAP Gold       Insight · AQE · MLOps
```

**Data Catalog** tetap modul inti (governance Metadata). **Dashboard & monitoring** ditambahkan sebagai modul embed agar pengguna tidak bolak-balik URL.

---

## 2. Struktur folder `portal-main/`

```
portal-main/
├── pages/
│   ├── index.tsx              # Overview portal
│   ├── catalog/               # Browse & lifecycle dataset
│   ├── lineage/               # Lineage graph
│   ├── kpi/                   # KPI IKU (Atlas)
│   ├── dashboards/            # Embed Superset + Grafana
│   │   ├── index.tsx          # Hub dashboard
│   │   ├── analitik.tsx
│   │   ├── insight.tsx
│   │   ├── monitoring-aqe.tsx
│   │   └── monitoring-mlops.tsx
│   └── api/atlas/             # Proxy REST ke Atlas
├── helpers/
│   ├── atlasApi.ts
│   └── dashboardPortal.ts     # URL embed Superset/Grafana
├── menu.ts                    # Sidebar: Catalog | Dashboards | Governance | Pipeline
└── components/
```

---

## 3. Menjalankan dengan Docker

```bash
cd Data-Lakehouse-Insight
./start.sh
# atau
docker compose up -d portal grafana superset atlas
```

| URL | Keterangan |
|-----|------------|
| http://localhost:13000 | Portal utama |
| http://localhost:13000/dashboards | Hub dashboard & monitoring |
| http://localhost:13000/catalog | Browse datasets |

Service Compose: **`portal`** · container: **`lhmeta-portal`** · volume: `./portal-main:/app`

---

## 4. Variabel lingkungan

| Variabel | Default | Keterangan |
|----------|---------|------------|
| `LHINSIGHT_PUBLIC_HOST` | `103.174.114.177` | IP/domain VM — dipakai portal & `GF_SERVER_ROOT_URL` Grafana |
| `LHINSIGHT_PORTAL_PORT` | `13000` | Port host (alias lama: `LHMETA_CATALOG_PORT`) |
| `LHINSIGHT_PORTAL_PRODUCTION` | `0` | `1` = `yarn build` + `next start` |
| `LHINSIGHT_PORTAL_ATLAS_URL` | `http://atlas:21000` | Atlas dari container (proxy API) |
| `LHINSIGHT_GRAFANA_PUBLIC_URL` | `http://<host>:13001` | Base URL Grafana (browser) |
| `LHINSIGHT_GRAFANA_EMBED_INSIGHT_URL` | — | URL lengkap dashboard Insight (dari Share di Grafana) |
| `LHINSIGHT_GRAFANA_EMBED_AQE_URL` | — | URL dashboard AQE Experiment |
| `LHINSIGHT_GRAFANA_EMBED_MLOPS_URL` | — | URL dashboard MLOps Pipeline |
| `LHINSIGHT_GRAFANA_EMBED_*_EXTERNAL_URL` | — | Tab baru (opsional, tanpa kiosk) |
| `LHINSIGHT_SUPERSET_PUBLIC_URL` | `http://<host>:18089` | URL browser untuk iframe Superset |
| `LHINSIGHT_PROMETHEUS_PUBLIC_URL` | `http://<host>:19090` | Opsional — link Prometheus |

Salin ke `.env` dari [`.env.example`](../../.env.example) — contoh untuk VM `103.179.57.24` sudah diisi di sana.

> **Penting:** URL harus yang dibuka **browser pengguna** (IP publik VM), bukan hostname Docker (`grafana`, `superset`).

Setelah ubah `.env`:

```bash
docker compose up -d grafana portal
# production portal: LHINSIGHT_PORTAL_PRODUCTION=1 docker compose up -d --build portal
```

---

## 5. Menu sidebar

| Seksi menu | Isi |
|------------|-----|
| **Catalog** | Dashboard, Browse, Lineage, KPI Dashboard |
| **Dashboards & Monitoring** | Portal overview, Analitik, Insight, AQE, MLOps |
| **Governance** | Classifications, Glossary, Data Quality |
| **Pipeline** | Medallion layers, UMT, Metadata Quality |

---

## 6. Embed Superset & Grafana

### URL dashboard (disarankan lewat `.env`)

| Halaman portal | Variabel `.env` |
|----------------|-----------------|
| `/dashboards/insight` | `LHINSIGHT_GRAFANA_EMBED_INSIGHT_URL` |
| `/dashboards/monitoring-aqe` | `LHINSIGHT_GRAFANA_EMBED_AQE_URL` |
| `/dashboards/monitoring-mlops` | `LHINSIGHT_GRAFANA_EMBED_MLOPS_URL` |

Salin URL dari Grafana → **Share** → browser link (termasuk slug `/d/<uid>/<slug>`). Portal menambahkan `&kiosk` otomatis pada iframe.

Fallback tanpa env: UID provisioned `lakehouse-dashboard-insight`, `lakehouse-aqe-experiment`, `lakehouse-mlops-pipeline`.

### Grafana gagal load di iframe

Pesan *"Grafana has failed to load its application files"* → set di `.env`:

- `LHINSIGHT_PUBLIC_HOST=<IP VM>`
- `LHINSIGHT_GRAFANA_PUBLIC_URL=http://<IP VM>:13001`

Lalu `docker compose up -d grafana` (`GF_SERVER_ROOT_URL` sudah di `docker-compose.yml`).

Jika pernah simpan URL lewat modal portal, hapus override lama: `rm -f portal-main/data/embed-config.json` lalu restart portal.

Grafana: `GF_SECURITY_ALLOW_EMBEDDING=true` (sudah di compose). Login iframe: **admin / admin**.

Detail KPI Gold & Superset: [`../gold-to-serving/README.md`](../gold-to-serving/README.md)  
Detail Grafana: [`../monitoring-grafana/README.md`](../monitoring-grafana/README.md)

---

## 7. Pengembangan lokal

```bash
cd portal-main
yarn install
NEXT_PUBLIC_ATLAS_URL=http://localhost:22100 \
NEXT_PUBLIC_GRAFANA_URL=http://localhost:13001 \
NEXT_PUBLIC_SUPERSET_URL=http://localhost:18089 \
yarn dev
```

Buka http://localhost:3000 (atau port dev Next.js).

---

## 8. Migrasi dari setup lama

| Sebelum | Sesudah |
|---------|---------|
| Folder `data-catalog-main/` | **`portal-main/`** (hapus folder/symlink lama) |
| Service `data-catalog` | `portal` |
| Container `lhmeta-data-catalog` | `lhmeta-portal` |
| Volume `catalog-node-modules` | `portal-node-modules` |

Jika container lama masih ada: `docker compose rm -f data-catalog` lalu `docker compose up -d portal`.

**IDE:** buka `portal-main/tsconfig.json` (bukan path `data-catalog-main`). Reload window Cursor setelah menghapus folder lama.

---

## 9. Dokumen terkait

| Topik | Lokasi |
|-------|--------|
| Star schema & dashboard analitik | [`../gold-to-serving/README.md`](../gold-to-serving/README.md) |
| Grafana & metrik MLOps | [`../monitoring-grafana/README.md`](../monitoring-grafana/README.md) |
| Eksperimen E2E | [`../eksperimen/README.md`](../eksperimen/README.md) |
| README utama repo | [`../../README.md`](../../README.md) |
