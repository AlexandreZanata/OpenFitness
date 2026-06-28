#!/usr/bin/env bash
# Gate N-04: verify NutriOffline fine-tuning dataset (Phase 4).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
VALIDATE="${NUTRI}/scripts/dataset/validate.py"
FOODS="${NUTRI}/data/processed/foods.parquet"
TRAIN="${NUTRI}/data/datasets/train.jsonl"

if [[ ! -f "${VENV}" ]]; then
    echo "ERROR: Phase 0 venv missing at ${NUTRI}/venv"
    exit 1
fi

if [[ ! -f "${FOODS}" ]]; then
    echo "ERROR: foods.parquet missing — run Phase 2 normalization first"
    exit 1
fi

if [[ ! -f "${TRAIN}" ]]; then
    echo "ERROR: train.jsonl missing — run: python ${NUTRI}/scripts/dataset/run_all.py"
    exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
python "${VALIDATE}"
echo "PASS: NutriOffline fine-tuning dataset gate (N-04)"
