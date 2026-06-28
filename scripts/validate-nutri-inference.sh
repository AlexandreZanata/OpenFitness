#!/usr/bin/env bash
# Gate N-06: verify NutriOffline GGUF inference (Phase 6).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
GGUF_DIR="${NUTRI}/models/gguf"
TEST="${NUTRI}/scripts/inference/test_inference.py"
BUILD="${NUTRI}/scripts/inference/build_llama_cpp.sh"
SERVE="${NUTRI}/scripts/inference/serve.sh"

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    exit 1
fi

GGUF="$(find "${GGUF_DIR}" -name '*.gguf' -type f 2>/dev/null | head -1)"
if [[ -z "${GGUF}" ]]; then
    echo "ERROR: GGUF missing — run: python ${NUTRI}/scripts/export/run_all.py"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"
export NUTRI_GGUF="${GGUF}"

bash "${BUILD}"

SERVER_PID=""
cleanup() {
    if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
        kill "${SERVER_PID}" 2>/dev/null || true
        wait "${SERVER_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT

bash "${SERVE}" > "${NUTRI}/logs/gate-llama-server.log" 2>&1 &
SERVER_PID=$!

python "${TEST}" --wait-server
echo "PASS: NutriOffline GGUF inference gate (N-06)"
