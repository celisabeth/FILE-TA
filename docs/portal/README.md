# InsightERA Portal (`portal-main`)

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
                    │   InsightERA Portal (:13000)        │
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
| `LHINSIGHT_PORTAL_PORT` | `13000` | Port host (alias lama: `LHMETA_CATALOG_PORT`) |
| `LHINSIGHT_PORTAL_PRODUCTION` | `0` | `1` = `yarn build` + `next start` |
| `LHINSIGHT_PORTAL_ATLAS_URL` | `http://atlas:21000` | Atlas dari container (proxy API) |
| `LHINSIGHT_GRAFANA_PUBLIC_URL` | `http://localhost:13001` | URL browser untuk iframe Grafana |
| `LHINSIGHT_SUPERSET_PUBLIC_URL` | `http://localhost:18089` | URL browser untuk iframe Superset |
| `LHINSIGHT_PROMETHEUS_PUBLIC_URL` | `http://localhost:19090` | Opsional — link Prometheus |

Salin ke `.env` dari [`.env.example`](../../.env.example).

> **Penting:** `NEXT_PUBLIC_*` harus URL yang dibuka **browser di mesin pengguna** (biasanya `localhost`), bukan hostname Docker internal (`grafana`, `superset`).

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

Konfigurasi UID Grafana (provisioned):

| Halaman portal | Dashboard Grafana |
|----------------|-------------------|
| `/dashboards/insight` | `lakehouse-dashboard-insight` |
| `/dashboards/monitoring-aqe` | `lakehouse-aqe-experiment` |
| `/dashboards/monitoring-mlops` | `lakehouse-mlops-pipeline` |

Grafana memerlukan `GF_SECURITY_ALLOW_EMBEDDING=true` (sudah di `docker-compose.yml`).

Login di iframe (sekali per layanan): **admin / admin**.

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

## 8. Migrasi dari `data-catalog-main`

| Sebelum | Sesudah |
|---------|---------|
| Folder `data-catalog-main/` | `portal-main/` |
| Service `data-catalog` | `portal` |
| Container `lhmeta-data-catalog` | `lhmeta-portal` |
| Volume `catalog-node-modules` | `portal-node-modules` |

Jika container lama masih ada: `docker compose rm -f data-catalog` lalu `docker compose up -d portal`.

**IDE / TypeScript:** folder `data-catalog-main` adalah symlink ke `portal-main` (kompatibilitas path lama). Buka workspace `Data-Lakehouse-Insight` atau folder `portal-main` langsung. Reload window jika error tsconfig masih muncul.

---

## 9. Dokumen terkait

| Topik | Lokasi |
|-------|--------|
| Star schema & dashboard analitik | [`../gold-to-serving/README.md`](../gold-to-serving/README.md) |
| Grafana & metrik MLOps | [`../monitoring-grafana/README.md`](../monitoring-grafana/README.md) |
| Eksperimen E2E | [`../eksperimen/README.md`](../eksperimen/README.md) |
| README utama repo | [`../../README.md`](../../README.md) |
