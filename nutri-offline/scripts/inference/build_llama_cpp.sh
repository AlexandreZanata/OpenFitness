#!/usr/bin/env bash
# Build or locate llama.cpp for NutriOffline (Phase 6 N-06-04).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LLAMA="${ROOT}/llama.cpp"
UNSLOTH_LLAMA="${HOME}/.unsloth/llama.cpp"
LINK_DIR="${LLAMA}/build/bin"

if [[ -x "${LLAMA}/build/bin/llama-server" ]]; then
    echo "PASS: llama.cpp already built at ${LLAMA}/build/bin/llama-server"
    "${LLAMA}/build/bin/llama-server" --version 2>/dev/null || true
    exit 0
fi

if [[ -x "${UNSLOTH_LLAMA}/llama-server" ]]; then
    echo "Using Unsloth prebuilt llama.cpp at ${UNSLOTH_LLAMA}"
    mkdir -p "${LINK_DIR}"
    ln -sf "${UNSLOTH_LLAMA}/llama-server" "${LINK_DIR}/llama-server"
    ln -sf "${UNSLOTH_LLAMA}/llama-cli" "${LINK_DIR}/llama-cli"
    echo "PASS: llama.cpp linked from Unsloth prebuild"
    "${LINK_DIR}/llama-server" --version 2>/dev/null || true
    exit 0
fi

if ! command -v cmake >/dev/null 2>&1; then
    echo "ERROR: cmake not found and no Unsloth prebuild — install cmake or run Unsloth GGUF export first"
    exit 1
fi

if [[ ! -d "${LLAMA}/.git" ]]; then
    echo "Cloning llama.cpp into ${LLAMA}..."
    git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "${LLAMA}"
fi

cmake -S "${LLAMA}" -B "${LLAMA}/build" -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build "${LLAMA}/build" --config Release -j"$(nproc)"

echo "PASS: llama.cpp built from source"
"${LLAMA}/build/bin/llama-server" --version 2>/dev/null || true
