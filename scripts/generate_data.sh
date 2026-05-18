#!/usr/bin/env bash
# Wrapper generate data staging — Data Lakehouse Insight
# Usage: ./scripts/generate_data.sh [opsi generate_bronze_data.py]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
GEN="$ROOT/scripts/generate_bronze_data.py"
COUNT="$ROOT/scripts/count_staging_rows.py"

usage() {
  cat <<'EOF'
Insight — generate data staging (CSV)

  ./scripts/generate_data.sh full              # --mode full --profile metadata (default)
  ./scripts/generate_data.sh full aqe          # profil AQE ~1M mahasiswa + skew SD
  ./scripts/generate_data.sh full insight      # E2E ringan ~200k baris + skew
  ./scripts/generate_data.sh append 5000       # tambah 5000 mahasiswa (+ turunan)
  ./scripts/generate_data.sh dry-run aqe       # rencana volume tanpa tulis file
  ./scripts/generate_data.sh count             # hitung baris CSV saat ini

Opsi lanjutan: python3 scripts/generate_bronze_data.py --help
Panduan: docs/generate-data/README.md
EOF
}

cmd="${1:-full}"
shift || true

case "$cmd" in
  -h|--help|help)
    usage
    exit 0
    ;;
  count|status)
    "$PYTHON" "$COUNT"
    exit 0
    ;;
  append)
    batch="${1:-5000}"
    echo "==> Append batch (mahasiswa=$batch)"
    "$PYTHON" "$GEN" --mode append --batch-size "$batch" "${@:2}"
    echo "==> Baris setelah append:"
    "$PYTHON" "$COUNT"
    ;;
  dry-run)
    profile="${1:-aqe}"
    "$PYTHON" "$GEN" --dry-run --profile "$profile" "${@:2}"
    ;;
  full)
    profile="${1:-metadata}"
    echo "==> Generate full profile=$profile"
    "$PYTHON" "$GEN" --mode full --profile "$profile" "${@:2}"
    echo "==> Ringkasan baris:"
    "$PYTHON" "$COUNT"
    ;;
  *)
    echo "Perintah tidak dikenal: $cmd"
    usage
    exit 1
    ;;
esac
