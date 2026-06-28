#!/usr/bin/env bash
# Gate RAG V2 Phase B: food aliases + hybrid lookup golden scenarios.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
ALIASES="${NUTRI}/data/processed/food_aliases.parquet"
INDEX="${NUTRI}/indexes/nutri-foods"

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

if [[ ! -f "${ALIASES}" ]]; then
    echo "Building food_aliases.parquet..."
    (cd "${NUTRI}" && python scripts/rag/build_food_aliases.py)
fi

(cd "${NUTRI}" && python -m unittest \
    tests.test_food_aliases \
    tests.test_hybrid_search \
    tests.test_lookup_golden \
    tests.test_response_cache \
    -v)

echo "Running RAG V2 benchmark (lookup-only if LLM offline)..."
(cd "${NUTRI}" && python scripts/app/benchmark_v2.py --skip-llm --repeats 1)

echo "PASS: NutriOffline RAG V2 gate (Phase B + C)"
