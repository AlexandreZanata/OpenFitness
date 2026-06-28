#!/usr/bin/env bash
# Gate N-02-06: verify NutriOffline normalized foods.parquet (Phase 2).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
VALIDATE="${NUTRI}/scripts/normalize/validate.py"

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    exit 1
fi

if [[ ! -f "${NUTRI}/data/processed/foods.parquet" ]]; then
    echo "ERROR: foods.parquet missing — run: python ${NUTRI}/scripts/normalize/run_all.py"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
python "${VALIDATE}"
echo "PASS: NutriOffline normalization gate (N-02-06)"
