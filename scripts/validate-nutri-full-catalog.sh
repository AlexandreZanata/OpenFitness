#!/usr/bin/env bash
# Phase 11 gate — full catalog index (N-11).
#   smoke  — v1-safe checks (default)
#   full   — strict gate after scope=all index build
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

echo "=== Generate / refresh fixtures ==="
python scripts/rag/generate_retrieval_corpus.py
python scripts/training/generate_domain_eval_v2.py

echo "=== Unit tests ==="
python -m unittest tests.test_full_catalog_coverage tests.test_retrieval_benchmark tests.test_eval_domain_v2 -q

echo "=== G-COV coverage report ==="
python scripts/rag/benchmark_coverage.py || true

if [[ "${MODE}" == "smoke" ]]; then
  echo "=== G-RET gate (current index) ==="
  python scripts/rag/benchmark_retrieval.py --gate || true
  echo "=== R-FULL-10 smoke ==="
  python scripts/app/test_r_full_10.py
  echo "PASS: Phase 11 smoke gate"
  exit 0
fi

echo "=== G-COV strict (require scope=all) ==="
python scripts/rag/benchmark_coverage.py --require-scope all

echo "=== G-RET strict ==="
python scripts/rag/benchmark_retrieval.py --gate

echo "=== G-PERF latency ==="
python scripts/rag/benchmark_latency.py --gate --samples 200

echo "=== G-DOM gate v2 (production RAG path) ==="
python scripts/training/eval_domain.py --fixture gate-v2 --require-rag --skip-training-check \
  --report-md "${NUTRI}/logs/eval-benchmark-v2-latest.md"

echo "=== R-FULL-10 full ==="
python scripts/app/test_r_full_10.py

echo "PASS: NutriOffline full catalog gate (N-11)"
