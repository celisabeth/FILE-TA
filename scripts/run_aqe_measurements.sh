#!/usr/bin/env bash
# Pengukuran AQE BAB IV §4.1.3–§4.1.6 (layer Silver)
# Usage:
#   ./scripts/run_aqe_measurements.sh              # di host (perlu Spark + data)
#   ./scripts/run_aqe_measurements.sh docker       # di dalam airflow-scheduler

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p metrics && chmod 1777 metrics 2>/dev/null || true

MODE="${1:-}"
CMD="${2:-all}"
if [[ "$MODE" == "docker" ]]; then
  DOCKER=1
  CMD="${2:-all}"
elif [[ "$MODE" == "partition-skew" || "$MODE" == "components" || "$MODE" == "format" || "$MODE" == "silver-summary" || "$MODE" == "all" ]]; then
  DOCKER=0
  CMD="$MODE"
else
  DOCKER=0
  CMD="${1:-all}"
fi

run_one() {
  if [[ "$DOCKER" == 1 ]]; then
    docker exec lhmeta-airflow-scheduler python /opt/airflow/scripts/benchmark/measure_aqe_experiment.py "$@"
  else
    PYTHONPATH=scripts python3 scripts/benchmark/measure_aqe_experiment.py "$@"
  fi
}

echo "=== Prasyarat: aqe_full_experiment sukses (Silver OFF/ON terisi) ==="

if [[ "$CMD" == "all" || "$CMD" == "partition-skew" ]]; then
  echo "=== 4.1.3 Distribusi partisi & skew ==="
  run_one partition-skew --aqe-scenario ON
fi
if [[ "$CMD" == "all" || "$CMD" == "components" ]]; then
  echo "=== 4.1.4 Efektivitas komponen AQE ==="
  run_one components --aqe-scenario ON \
    --profiles OFF,ON_FULL,ON_COALESCE_ONLY,ON_SKEW_ONLY,ON_DPP_ONLY,ON_LOCAL_SHUFFLE_ONLY
fi
if [[ "$CMD" == "all" || "$CMD" == "format" ]]; then
  echo "=== 4.1.5 Perbandingan format data ==="
  run_one format --aqe-scenario ON --sample-rows 50000
fi
if [[ "$CMD" == "all" || "$CMD" == "silver-summary" ]]; then
  echo "=== 4.1.6 Ringkasan layer Silver ==="
  run_one silver-summary --aqe-scenario ON
fi

echo "=== Selesai. Artefak: metrics/aqe_measurement_*.json ==="
ls -la metrics/aqe_measurement_*.json 2>/dev/null | tail -10
