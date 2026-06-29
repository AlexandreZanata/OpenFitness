#!/usr/bin/env bash
# Gate N-07: verify NutriOffline end-to-end offline assistant (Phase 7).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
E2E="${NUTRI}/scripts/app/test_offline_e2e.py"
START="${NUTRI}/scripts/app/start_offline.sh"
STOP="${NUTRI}/scripts/app/stop_offline.sh"
INDEX="${NUTRI}/indexes/nutri-foods"
GGUF_DIR="${NUTRI}/models/gguf"

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    exit 1
fi

if [[ ! -d "${INDEX}" ]]; then
    echo "ERROR: RAG index missing — run Phase 3"
    exit 1
fi

GGUF="$(find "${GGUF_DIR}" -name '*.gguf' -type f 2>/dev/null | head -1)"
if [[ -z "${GGUF}" ]]; then
    echo "ERROR: GGUF missing — run Phase 6 export"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"
export NUTRI_GGUF="${GGUF}"

bash "${STOP}" 2>/dev/null || true
bash "${START}" > /dev/null

python "${E2E}"
python -m unittest tests.test_admin_mobile_parity -q
echo "PASS: NutriOffline app integration gate (N-07)"
