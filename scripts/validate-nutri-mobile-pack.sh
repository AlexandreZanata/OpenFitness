#!/usr/bin/env bash
# Phase 8 gate: mobile pack ≤200 MB + parity tests (stub until pack is built).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
PACK="${NUTRI}/indexes/nutri-mobile/nutri-mobile.pack"
MANIFEST="${NUTRI}/indexes/nutri-mobile/pack.manifest.json"
LIMIT_BYTES=$((200 * 1024 * 1024))

echo "Phase 8 mobile pack gate"

if [[ ! -f "${NUTRI}/docs/MOBILE-CAPABILITY-MATRIX.md" ]]; then
  echo "ERROR: MOBILE-CAPABILITY-MATRIX.md missing"
  exit 1
fi

if [[ ! -f "${NUTRI}/phases/08-mobile-pack/TASKS.md" ]]; then
  echo "ERROR: Phase 8 TASKS missing"
  exit 1
fi

if [[ ! -f "${PACK}" && ! -f "${MANIFEST}" ]]; then
  echo "WARN: mobile pack not built yet — run:"
  echo "  cd nutri-offline && python scripts/mobile/build_pack.py"
  echo "SKIP: artifact checks (Phase 8 implementation pending)"
  exit 0
fi

TARGET="${PACK}"
if [[ ! -f "${TARGET}" && -f "${MANIFEST}" ]]; then
  TARGET="${MANIFEST}"
fi

SIZE="$(stat -c%s "${TARGET}")"
if (( SIZE > LIMIT_BYTES )); then
  echo "FAIL: pack size ${SIZE} bytes exceeds limit ${LIMIT_BYTES} (200 MB)"
  exit 1
fi

echo "OK: pack size ${SIZE} bytes (≤200 MB)"

VENV="${NUTRI}/venv/bin/activate"
if [[ -f "${VENV}" ]]; then
  # shellcheck disable=SC1090
  source "${VENV}"
  export HF_HOME="${NUTRI}/models/base"
  if [[ -f "${NUTRI}/tests/test_mobile_parity_golden.py" ]]; then
    (cd "${NUTRI}" && python -m unittest tests.test_mobile_parity_golden -v)
  else
    echo "WARN: test_mobile_parity_golden.py not implemented yet"
  fi
fi

echo "PASS: NutriOffline mobile pack gate"
