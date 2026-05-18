#!/usr/bin/env bash
# Fix bind-mounted ./metrics before Airflow drops to user airflow (UID 50000).
set -euo pipefail

METRICS_DIR="${META_METRICS_DIR:-/opt/airflow/metrics}"

fix_metrics_dir() {
  mkdir -p "${METRICS_DIR}"
  if [ "$(id -u)" -eq 0 ]; then
    chown -R "${AIRFLOW_UID:-50000}:${AIRFLOW_GID:-0}" "${METRICS_DIR}" 2>/dev/null || true
    chmod 1777 "${METRICS_DIR}" 2>/dev/null || true
  else
    chmod 1777 "${METRICS_DIR}" 2>/dev/null || true
  fi
}

fix_metrics_dir

if [ -x /usr/bin/dumb-init ]; then
  exec /usr/bin/dumb-init -- /entrypoint "$@"
fi
exec /entrypoint "$@"
