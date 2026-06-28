#!/usr/bin/env bash
# Gate N-05-preflight: verify NutriOffline training preflight (Phase 5 Block B/C).
# Does not run full multi-epoch training — use train_qlora.py for that.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
PREFLIGHT="${NUTRI}/scripts/training/preflight.py"
CONFIG="${NUTRI}/scripts/training/config.yaml"

echo "== NutriOffline training preflight gate (N-05) =="

"${ROOT}/scripts/validate-nutri-hardware.sh"
"${ROOT}/scripts/validate-nutri-dataset.sh"

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    exit 1
fi

if [[ ! -f "${PREFLIGHT}" ]]; then
    echo "ERROR: preflight.py missing — implement Phase 5 Block B first"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"
export UNSLOTH_USE_FP16=1

python "${NUTRI}/scripts/validate_environment.py"
python "${PREFLIGHT}" --config "${CONFIG}"

echo "PASS: NutriOffline training preflight gate (N-05)"
