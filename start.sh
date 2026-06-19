#!/usr/bin/env bash
# ============================================================
#  Lakehouse Metadata Pipeline — Full Startup Script
#  Stack: Spark | Airflow | MinIO | Atlas | Hive | Iceberg
#         Jupyter | insightera Portal (Next.js — portal-main)
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p metrics data/staging
chmod 1777 metrics 2>/dev/null || sudo chmod 1777 metrics 2>/dev/null || true

STEP=0
TOTAL=10

step() {
  STEP=$((STEP + 1))
  echo ""
  echo -e "${BLUE}[${STEP}/${TOTAL}]${NC} ${BOLD}$1${NC}"
}

wait_healthy() {
  local name="$1" max="${2:-60}" i=0
  while [ $i -lt $max ]; do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null || echo "missing")
    case "$status" in
      healthy) echo -e "  ${GREEN}✅ $name healthy${NC}"; return 0 ;;
      unhealthy) echo -e "  ${YELLOW}⚠️  $name unhealthy (continuing)${NC}"; return 0 ;;
      missing)   echo -e "  ${RED}❌ $name not found${NC}"; return 1 ;;
    esac
    sleep 5; i=$((i + 5))
    echo -ne "  ⏳ Waiting for $name... (${i}s/${max}s)\r"
  done
  echo -e "  ${YELLOW}⚠️  $name timeout after ${max}s (continuing)${NC}"
}

wait_running() {
  local name="$1" max="${2:-30}" i=0
  while [ $i -lt $max ]; do
    running=$(docker inspect --format='{{.State.Running}}' "$name" 2>/dev/null || echo "false")
    [ "$running" = "true" ] && echo -e "  ${GREEN}✅ $name running${NC}" && return 0
    sleep 3; i=$((i + 3))
  done
  echo -e "  ${YELLOW}⚠️  $name not running after ${max}s${NC}"
}

# Hive Metastore: init schema + Thrift bind bisa >60s pada first run / VM lambat
wait_hive_metastore() {
  local max="${1:-150}" i=0
  local port="${LHMETA_HIVE_METASTORE_PORT:-19083}"
  echo -e "  ${YELLOW}Hive Metastore: init schema + Thrift (bisa 1–2 menit pertama kali)${NC}"
  while [ $i -lt $max ]; do
    status=$(docker inspect --format='{{.State.Health.Status}}' lhmeta-hive-metastore 2>/dev/null || echo "missing")
    if [ "$status" = "healthy" ]; then
      echo -e "  ${GREEN}✅ lhmeta-hive-metastore healthy (Docker healthcheck)${NC}"
      return 0
    fi
    if docker exec lhmeta-hive-metastore bash -c 'echo > /dev/tcp/127.0.0.1/9083' 2>/dev/null; then
      echo -e "  ${GREEN}✅ lhmeta-hive-metastore Thrift :9083 OK (probe)${NC}"
      return 0
    fi
    if bash -c "echo > /dev/tcp/127.0.0.1/${port}" 2>/dev/null; then
      echo -e "  ${GREEN}✅ lhmeta-hive-metastore reachable on host :${port}${NC}"
      return 0
    fi
    sleep 5
    i=$((i + 5))
    echo -ne "  ⏳ Hive Metastore... (${i}s/${max}s, status=${status})\r"
  done
  echo ""
  echo -e "  ${YELLOW}⚠️  Hive Metastore belum terdeteksi setelah ${max}s — cek: docker logs lhmeta-hive-metastore${NC}"
  echo -e "  ${YELLOW}   Jika log sudah 'Starting Hive Metastore Server', lanjutkan manual atau tunggu lalu: nc -zv localhost ${port}${NC}"
}

print_banner() {
  echo -e "${CYAN}"
  cat << 'EOF'
  ██╗      █████╗ ██╗  ██╗███████╗██╗  ██╗ ██████╗ ██╗   ██╗███████╗███████╗
  ██║     ██╔══██╗██║ ██╔╝██╔════╝██║  ██║██╔═══██╗██║   ██║██╔════╝██╔════╝
  ██║     ███████║█████╔╝ █████╗  ███████║██║   ██║██║   ██║███████╗█████╗
  ██║     ██╔══██║██╔═██╗ ██╔══╝  ██╔══██║██║   ██║██║   ██║╚════██║██╔══╝
  ███████╗██║  ██║██║  ██╗███████╗██║  ██║╚██████╔╝╚██████╔╝███████║███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝
              Data Lakehouse — Metadata Pipeline + Data Catalog
EOF
  echo -e "${NC}"
}

# ────────────────────────────────────────────────────────────

print_banner

# ── 1. Pre-flight checks ───────────────────────────────────
step "Pre-flight checks"
if ! command -v docker &>/dev/null; then
  echo -e "${RED}Docker not found! Install Docker first.${NC}"; exit 1
fi
if ! docker compose version &>/dev/null 2>&1; then
  echo -e "${RED}Docker Compose not found!${NC}"; exit 1
fi
echo -e "  ${GREEN}✅ Docker + Compose OK${NC}"
echo -e "  ${YELLOW}Recommended: 8GB+ RAM, 15GB+ disk${NC}"

# ── 2. Download required JARs ──────────────────────────────
step "Downloading required JARs (Hive + Spark)"
mkdir -p lib
JARS=(
  "postgresql-42.6.0.jar|https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar"
  "hadoop-aws-3.3.4.jar|https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar"
  "aws-java-sdk-bundle-1.12.262.jar|https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar"
  "iceberg-spark-runtime-3.5_2.12-1.5.2.jar|https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.2/iceberg-spark-runtime-3.5_2.12-1.5.2.jar"
)
for entry in "${JARS[@]}"; do
  jar="${entry%%|*}"; url="${entry##*|}"
  if [ ! -f "lib/$jar" ]; then
    echo -e "  Downloading $jar ..."
    curl -fSL -o "lib/$jar" "$url"
  else
    echo -e "  ${GREEN}✓${NC} $jar (cached)"
  fi
done
echo -e "  ${GREEN}✅ All JARs ready${NC}"

# ── 3. Build custom images ─────────────────────────────────
step "Building custom Docker images (Airflow)"
docker compose build airflow-init airflow-webserver airflow-scheduler 2>&1 | tail -5
echo -e "  ${GREEN}✅ Airflow image built${NC}"

# ── 4. Pull remaining images ──────────────────────────────
step "Pulling Docker images"
docker compose pull 2>&1 | grep -E "Pulling|Pull|complete|error" || true
echo -e "  ${GREEN}✅ Images ready${NC}"

# ── 5. Infrastructure layer ───────────────────────────────
step "Starting infrastructure (PostgreSQL, ZooKeeper, Kafka)"
docker compose up -d postgres zookeeper kafka
wait_healthy lhmeta-postgres 30
wait_healthy lhmeta-zookeeper 30
wait_healthy lhmeta-kafka 40

echo -e "  Creating required databases..."
docker exec lhmeta-postgres psql -U admin -d postgres -c "CREATE DATABASE metastore_db;" 2>/dev/null || true
docker exec lhmeta-postgres psql -U admin -d postgres -c "CREATE DATABASE iceberg_catalog;" 2>/dev/null || true
docker exec lhmeta-postgres psql -U admin -d postgres -c "CREATE DATABASE airflow_db;" 2>/dev/null || true
echo -e "  ${GREEN}✅ Databases: metastore_db, iceberg_catalog, airflow_db${NC}"

# ── 6. Storage + Catalog backends ─────────────────────────
step "Starting HBase, Solr, MinIO"
docker compose up -d hbase solr minio
sleep 10
docker compose up -d minio-init
wait_healthy lhmeta-minio 30
wait_healthy lhmeta-solr 40
wait_healthy lhmeta-hbase 60

echo -e "  Starting Solr Atlas init..."
docker compose up -d solr-atlas-init
sleep 15
echo -e "  ${GREEN}✅ Storage + catalog backends ready${NC}"

# ── 7. Metastore + Iceberg + Atlas ────────────────────────
step "Starting Hive Metastore, Iceberg REST, Atlas"
docker compose up -d hive-metastore
wait_hive_metastore 150

docker compose up -d iceberg-rest
sleep 5
wait_healthy lhmeta-iceberg-rest 45

docker compose up -d atlas
echo -e "  ${YELLOW}Atlas needs several minutes to warm up (HBase + Solr + JanusGraph)${NC}"

# ── 8. Compute layer ─────────────────────────────────────
step "Starting Spark cluster + Jupyter"
docker compose up -d spark-master
wait_healthy lhmeta-spark-master 30
docker compose up -d spark-worker-1 spark-worker-2
docker compose up -d jupyter
sleep 5
echo -e "  ${GREEN}✅ Spark cluster + Jupyter ready${NC}"

# ── 9. Orchestration ─────────────────────────────────────
step "Starting Airflow (init + webserver + scheduler)"
docker compose run --rm metrics-init 2>/dev/null || true
for db in airflow_db iceberg_catalog superset_db mlflow_db; do
  docker exec lhmeta-postgres psql -U admin -d postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname='${db}'" 2>/dev/null | grep -q 1 \
    || docker exec lhmeta-postgres psql -U admin -d postgres -c "CREATE DATABASE ${db};" 2>/dev/null \
    || true
done
docker compose rm -f airflow-init 2>/dev/null || true
if ! docker compose run --rm airflow-init; then
  echo -e "  ${RED}❌ airflow-init failed — see: docker compose logs airflow-init${NC}"
  docker compose logs --tail 80 airflow-init 2>/dev/null || true
else
  echo -e "  ${GREEN}✅ Airflow DB migrated${NC}"
fi
docker compose up -d airflow-webserver
wait_healthy lhmeta-airflow-webserver 90
docker compose up -d airflow-scheduler
sleep 5
echo -e "  ${GREEN}✅ Airflow ready (UI :18681 — airflow / airflow)${NC}"

step "Starting MLflow (wajib untuk mlops_pipeline train_models)"
docker compose up -d mlflow 2>/dev/null || true
sleep 5
echo -e "  ${GREEN}✅ MLflow UI :15500 (tracking URI di Airflow: http://mlflow:5000)${NC}"

# ── 10. insightera Portal (Next.js) ─────────────────────
step "Starting insightera Portal (portal-main)"
docker compose up -d portal 2>/dev/null || echo -e "  ${YELLOW}portal service not configured (optional)${NC}"
sleep 3
echo -e "  ${GREEN}✅ Portal started (if configured)${NC}"

# ── Generate staging data if not exists ──────────────────
if [ ! -f data/staging/raw_mahasiswa.csv ]; then
  echo ""
  echo -e "${YELLOW}No staging data found. Generating synthetic data...${NC}"
  ./scripts/generate_data.sh full 2>/dev/null || \
    python3 scripts/generate_bronze_data.py --mode full --profile real 2>/dev/null || \
    echo -e "${YELLOW}  Skipped — run: ./scripts/generate_data.sh full  (see docs/generate-data/)${NC}"
fi

# ── Final status ─────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  SERVICE STATUS${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | head -25 || docker compose ps
echo ""

echo -e "${CYAN}${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  SERVICE UI ACCESS POINTS${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}Spark Master UI${NC}        ${GREEN}http://localhost:18080${NC}"
echo -e "  ${YELLOW}Airflow${NC}                ${GREEN}http://localhost:18681${NC}    (airflow / airflow)"
echo -e "  ${YELLOW}MinIO Console${NC}          ${GREEN}http://localhost:19001${NC}    (minioadmin / minioadmin123)"
echo -e "  ${YELLOW}MinIO S3 API${NC}           ${GREEN}http://localhost:19000${NC}"
echo -e "  ${YELLOW}HBase Master UI${NC}        ${GREEN}http://localhost:19010${NC}"
echo -e "  ${YELLOW}Apache Solr${NC}            ${GREEN}http://localhost:18984${NC}"
echo -e "  ${YELLOW}Apache Atlas${NC}           ${GREEN}http://localhost:22100${NC}    (admin / admin)"
echo -e "  ${YELLOW}Hive Metastore${NC}         ${GREEN}thrift://localhost:19083${NC}"
echo -e "  ${YELLOW}Iceberg REST Catalog${NC}   ${GREEN}http://localhost:18181${NC}"
echo -e "  ${YELLOW}Jupyter Notebook${NC}       ${GREEN}http://localhost:18888${NC}    (token: lakehouse)"
echo -e "  ${YELLOW}insightera Portal${NC}      ${GREEN}http://localhost:13000${NC}  ${YELLOW}(/catalog · /dashboards)${NC}"
echo -e "  ${YELLOW}MLflow${NC}                 ${GREEN}http://localhost:15500${NC}    (model registry MLOps)"
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Quick Commands:${NC}"
echo -e "  ${BLUE}docker compose ps${NC}                           # Status all services"
echo -e "  ${BLUE}docker compose logs -f atlas${NC}                # Atlas logs"
echo -e "  ${BLUE}docker compose logs -f airflow-scheduler${NC}    # Airflow logs"
echo -e "  ${BLUE}docker compose down${NC}                         # Stop all"
echo -e "  ${BLUE}docker compose down -v${NC}                      # Stop + remove volumes"
echo ""
echo -e "  ${BOLD}Run Pipelines:${NC}"
echo -e "  ${BLUE}docker exec lhmeta-airflow-scheduler airflow dags trigger staging_to_bronze_pipeline${NC}"
echo -e "  ${BLUE}docker exec lhmeta-airflow-scheduler airflow dags trigger bronze_to_silver_pipeline${NC}"
echo -e "  ${BLUE}docker exec lhmeta-airflow-scheduler airflow dags trigger silver_to_gold_pipeline${NC}"
echo ""
echo -e "${GREEN}${BOLD}Lakehouse stack fully started!${NC}"
