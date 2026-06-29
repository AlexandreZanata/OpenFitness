#!/usr/bin/env bash
# Gate N-05-post: verify NutriOffline QLoRA training completed (Phase 5 Block E).
# Checks adapter, training loss stability, and domain eval pass criteria.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
ADAPTER="${NUTRI_ADAPTER_DIR:-${NUTRI}/models/adapters/nutri-qwen25-3b-v2}"
EVAL="${NUTRI}/scripts/training/eval_domain.py"
CONFIG="${NUTRI}/scripts/training/config.yaml"
GATE_PROMPTS="${NUTRI}/tests/fixtures/domain_eval_gate.jsonl"

echo "== NutriOffline training post-train gate (N-05) =="

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    exit 1
fi

if [[ ! -f "${ADAPTER}/adapter_model.safetensors" ]]; then
    echo "ERROR: adapter missing at ${ADAPTER}"
    echo "Run: python ${NUTRI}/scripts/training/train_qlora.py --config ${CONFIG}"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"
export UNSLOTH_USE_FP16=1

python "${EVAL}" --config "${CONFIG}" --prompts "${GATE_PROMPTS}"

echo "PASS: NutriOffline training post-train gate (N-05)"
