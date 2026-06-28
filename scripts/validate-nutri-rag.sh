#!/usr/bin/env bash
# Gate N-03-05: verify NutriOffline LanceDB RAG index (Phase 3).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/.local/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
INDEX="${NUTRI}/indexes/nutri-foods"
TEST="${NUTRI}/scripts/rag/test_queries.py"

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    exit 1
fi

if [[ ! -d "${INDEX}" ]]; then
    echo "ERROR: RAG index missing — run: python ${NUTRI}/scripts/rag/run_all.py"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"
python "${TEST}"
echo "PASS: NutriOffline RAG gate (N-03-05)"
