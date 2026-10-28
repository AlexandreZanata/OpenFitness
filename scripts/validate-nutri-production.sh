#!/usr/bin/env bash
# Production gate: v2 index metadata, v1 GGUF, RAG V2 golden + benchmark.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
VENV="${NUTRI}/venv/bin/activate"
INDEX_META="${NUTRI}/indexes/nutri-foods/metadata.json"
GGUF_V1="${NUTRI}/models/gguf/nutri-qwen25-3b-v1-q4_k_m.gguf"
ADAPTER_V1="${NUTRI}/models/adapters/nutri-qwen25-3b-v1"

if [[ ! -f "${VENV}" ]]; then
  echo "ERROR: venv missing at ${NUTRI}/venv"
  exit 1
fi

# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"
export NUTRI_ADAPTER=nutri-qwen25-3b-v1

echo "Checking production artifacts..."
if [[ ! -d "${ADAPTER_V1}" ]]; then
  echo "ERROR: Phase 5 adapter missing at ${ADAPTER_V1}"
  exit 1
fi

if [[ ! -f "${GGUF_V1}" ]]; then
  LEGACY="${NUTRI}/models/gguf/nutri-qwen25-3b-nutri-qwen25-3b-v1-q4_k_m.gguf"
  if [[ -f "${LEGACY}" ]]; then
    ln -sf "$(basename "${LEGACY}")" "${GGUF_V1}"
    echo "Created GGUF symlink for production"
  else
    echo "ERROR: production GGUF missing at ${GGUF_V1}"
    exit 1
  fi
fi

if [[ -f "${INDEX_META}" ]]; then
  python - "${INDEX_META}" <<'PY'
import json
import sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
version = meta.get("schema_version", 1)
if version < 2:
    print(f"WARN: index schema_version={version} (v2 recommended — run setup_production.sh)")
else:
    print(f"OK: index schema_version={version}, fts_index={meta.get('fts_index')}")
PY
fi

bash "${ROOT}/scripts/validate-nutri-rag-v2.sh"

echo "Checking GGUF path resolution..."
python - "${NUTRI}" <<'PY'
import importlib.util
import os
import sys
from pathlib import Path

nutri = Path(sys.argv[1])
export_paths = nutri / "scripts/export/_paths.py"
spec = importlib.util.spec_from_file_location("export_paths", export_paths)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
os.environ.setdefault("NUTRI_ADAPTER", "nutri-qwen25-3b-v1")
spec.loader.exec_module(mod)
assert mod.GGUF_PATH.name == "nutri-qwen25-3b-v1-q4_k_m.gguf", mod.GGUF_PATH.name
assert mod.GGUF_PATH.is_file(), f"missing {mod.GGUF_PATH}"
print(f"OK: GGUF path {mod.GGUF_PATH}")
PY

echo "PASS: NutriOffline production gate"
