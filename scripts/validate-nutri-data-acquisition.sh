#!/usr/bin/env bash
# Gate N-01-08: verify NutriOffline raw data sources (Phase 1).
# Requires Phase 0 venv and completed downloads under nutri-offline/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
SMOKE="${NUTRI}/scripts/smoke_read_sources.py"

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    echo "Hint: complete Phase 0 first — see docs/nutri-offline-local.md"
    exit 1
fi

if [[ ! -f "${NUTRI}/data/raw/manifest.json" ]]; then
    echo "ERROR: manifest.json missing — run: python ${NUTRI}/scripts/download/run_all.py"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
python "${SMOKE}"
echo "PASS: NutriOffline data acquisition gate (N-01-08)"
