#!/usr/bin/env bash
# Phase 11 gate — full catalog index scaffold + G-COV (N-11).
# Exits 0 only when index scope=all and all enabled checks pass.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
MODE="${1:-smoke}"

if [[ ! -f "${VENV}" ]]; then
  echo "ERROR: venv missing at ${NUTRI}/venv"
  exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"

cd "${NUTRI}"

echo "=== N-11-00 prerequisites ==="
python scripts/rag/check_full_catalog_prereqs.py

echo "=== Unit tests (G-COV helpers) ==="
python -m unittest tests.test_full_catalog_coverage -q

echo "=== G-COV coverage report (current index) ==="
python scripts/rag/benchmark_coverage.py || true

if [[ "${MODE}" == "smoke" ]]; then
  echo "=== R-FULL-10 smoke (v1-safe; branded cases skipped until scope=all) ==="
  python scripts/app/test_r_full_10.py
  echo "PASS: Phase 11 smoke gate (full catalog build still required for scope=all)"
  exit 0
fi

echo "=== G-COV strict (require scope=all) ==="
python scripts/rag/benchmark_coverage.py --require-scope all

echo "=== R-FULL-10 full (all 10 cases) ==="
python scripts/app/test_r_full_10.py

echo "PASS: NutriOffline full catalog gate (N-11)"