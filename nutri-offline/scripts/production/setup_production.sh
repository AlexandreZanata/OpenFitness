#!/usr/bin/env bash
# NutriOffline production setup — v2 index, embedder A/B, v1 GGUF wiring.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${ROOT}"

SKIP_INDEX="${SKIP_INDEX:-0}"
SKIP_EMBEDDER_AB="${SKIP_EMBEDDER_AB:-0}"
DEVICE="${NUTRI_INDEX_DEVICE:-cuda}"
ADAPTER="${NUTRI_ADAPTER:-nutri-qwen25-3b-v1}"
QUANT="${NUTRI_GGUF_QUANT:-q4_k_m}"

if [[ ! -f "${ROOT}/venv/bin/activate" ]]; then
  echo "ERROR: venv missing — run Phase 0 setup first"
  exit 1
fi

# shellcheck disable=SC1091
source "${ROOT}/venv/bin/activate"
export HF_HOME="${ROOT}/models/base"
export NUTRI_ADAPTER="${ADAPTER}"
export NUTRI_GGUF_QUANT="${QUANT}"

echo "=== 1/5 Food aliases ==="
python scripts/rag/build_food_aliases.py

echo "=== 2/5 GGUF symlink (legacy double-prefix fix) ==="
GGUF_DIR="${ROOT}/models/gguf"
CANONICAL="${GGUF_DIR}/nutri-qwen25-3b-v1-${QUANT}.gguf"
LEGACY="${GGUF_DIR}/nutri-qwen25-3b-nutri-qwen25-3b-v1-${QUANT}.gguf"
if [[ -f "${CANONICAL}" ]]; then
  echo "Production GGUF present: ${CANONICAL}"
elif [[ -f "${LEGACY}" ]]; then
  ln -sf "$(basename "${LEGACY}")" "${CANONICAL}"
  echo "Linked ${CANONICAL} -> $(basename "${LEGACY}")"
else
  echo "WARN: production GGUF not found — export with:"
  echo "  NUTRI_ADAPTER=${ADAPTER} python scripts/export/run_all.py --skip-merge"
fi

if [[ "${SKIP_INDEX}" != "1" ]]; then
  echo "=== 3/5 LanceDB index v2 rebuild (device=${DEVICE}) ==="
  python scripts/rag/build_index_v2.py --scope v1 --device "${DEVICE}" --skip-aliases
else
  echo "=== 3/5 Skipping index rebuild (SKIP_INDEX=1) ==="
fi

if [[ "${SKIP_EMBEDDER_AB}" != "1" ]]; then
  echo "=== 4/5 Embedder A/B benchmark ==="
  python scripts/rag/embedder_benchmark.py --device cpu --runs 2 \
    --models BAAI/bge-m3 BAAI/bge-small-en-v1.5
else
  echo "=== 4/5 Skipping embedder A/B (SKIP_EMBEDDER_AB=1) ==="
fi

echo "=== 5/5 Production validation gate ==="
bash "${ROOT}/../scripts/validate-nutri-production.sh"

echo ""
echo "PASS: NutriOffline production setup complete"
echo "Start chat: bash scripts/app/start_chat.sh"
