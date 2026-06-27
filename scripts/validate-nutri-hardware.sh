#!/usr/bin/env bash
# Gate N-00-01: verify NVIDIA GPU is present for NutriOffline local ML (Phase 0).
# Does not require Python — safe to run before venv setup.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MIN_VRAM_MIB=7500

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found — install NVIDIA drivers (Pop!_OS: nvidia-driver-*)"
    exit 1
fi

GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | xargs)"
VRAM_TOTAL="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | tr -d ' ')"
VRAM_FREE="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1 | tr -d ' ')"

echo "OK: GPU detected — ${GPU_NAME}"
echo "OK: VRAM total ${VRAM_TOTAL} MiB, free ${VRAM_FREE} MiB"

if (( VRAM_TOTAL < MIN_VRAM_MIB )); then
    echo "ERROR: need >= ${MIN_VRAM_MIB} MiB VRAM for QLoRA (got ${VRAM_TOTAL} MiB)"
    exit 1
fi

NUTRI_OFFLINE="${ROOT}/.local/nutri-offline"
if [[ -d "${NUTRI_OFFLINE}/venv" ]]; then
    echo "Hint: run full checks with:"
    echo "  source ${NUTRI_OFFLINE}/venv/bin/activate && python ${NUTRI_OFFLINE}/scripts/validate_environment.py"
else
    echo "Hint: Phase 0 venv not found at ${NUTRI_OFFLINE}/venv — see docs/nutri-offline-local.md"
fi

echo "PASS: NutriOffline hardware gate (N-00-01)"
