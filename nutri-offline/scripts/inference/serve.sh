#!/usr/bin/env bash
# Start llama.cpp OpenAI-compatible server (Phase 6 N-06-05).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
QUANT="${NUTRI_GGUF_QUANT:-q4_k_m}"
ADAPTER="${NUTRI_ADAPTER:-smoke-test}"
GGUF="${NUTRI_GGUF:-${ROOT}/models/gguf/nutri-qwen25-3b-${ADAPTER}-${QUANT}.gguf}"
HOST="${NUTRI_INFERENCE_HOST:-127.0.0.1}"
PORT="${NUTRI_INFERENCE_PORT:-8080}"
SERVER="${ROOT}/llama.cpp/build/bin/llama-server"

if [[ ! -f "${GGUF}" ]]; then
    # Try any gguf in models/gguf
    GGUF="$(find "${ROOT}/models/gguf" -name '*.gguf' -type f 2>/dev/null | head -1)"
fi

if [[ ! -f "${GGUF}" ]]; then
    echo "ERROR: GGUF missing — run scripts/export/run_all.py first"
    exit 1
fi

if [[ ! -x "${SERVER}" ]]; then
    echo "ERROR: llama-server missing — run scripts/inference/build_llama_cpp.sh"
    exit 1
fi

echo "Starting llama-server on ${HOST}:${PORT}"
echo "Model: ${GGUF}"
exec "${SERVER}" \
    -m "${GGUF}" \
    --host "${HOST}" \
    --port "${PORT}" \
    -c 4096 \
    -ngl 99
