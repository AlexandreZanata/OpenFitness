#!/usr/bin/env bash
# Phase 8 gate: mobile pack ≤200 MB + manifest checksums + parity tests.
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

if [[ ! -f "${MANIFEST}" ]]; then
  echo "ERROR: pack manifest missing — run:"
  echo "  cd nutri-offline && python scripts/mobile/build_pack.py"
  exit 1
fi

if [[ ! -f "${PACK}" ]]; then
  echo "ERROR: nutri-mobile.pack missing"
  exit 1
fi

SIZE="$(stat -c%s "${PACK}")"
if (( SIZE > LIMIT_BYTES )); then
  echo "FAIL: pack size ${SIZE} bytes exceeds limit ${LIMIT_BYTES} (200 MB)"
  exit 1
fi
echo "OK: pack size ${SIZE} bytes (≤200 MB)"

VENV="${NUTRI}/venv/bin/activate"
if [[ ! -f "${VENV}" ]]; then
  echo "ERROR: venv missing at ${VENV}"
  exit 1
fi
# shellcheck disable=SC1090
source "${VENV}"
export HF_HOME="${NUTRI}/models/base"
export NUTRI_ROOT="${NUTRI}"

python - <<PY
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

nutri = Path(os.environ["NUTRI_ROOT"])
manifest_path = nutri / "indexes/nutri-mobile/pack.manifest.json"
pack_path = nutri / "indexes/nutri-mobile/nutri-mobile.pack"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

sys.path.insert(0, str(nutri / "scripts/mobile"))
from pack_budget import validate_manifest, validate_pack_size

errors = validate_manifest(manifest)
if errors:
    print("FAIL: manifest validation:", errors)
    sys.exit(1)

validate_pack_size(manifest["size_bytes"])

with tarfile.open(pack_path, "r:xz") as archive:
    members = {member.name: member for member in archive.getmembers() if member.isfile()}
    for entry in manifest.get("files", []):
        name = entry["path"]
        if name not in members:
            print(f"FAIL: missing file in pack: {name}")
            sys.exit(1)
        extracted = archive.extractfile(members[name])
        assert extracted is not None
        digest = hashlib.sha256(extracted.read()).hexdigest()
        if digest != entry["sha256"]:
            print(f"FAIL: checksum mismatch for {name}")
            sys.exit(1)

print("OK: manifest checksums match pack contents")
PY

(cd "${NUTRI}" && python -m unittest \
  tests.test_mobile_intent \
  tests.test_mobile_reasoning \
  tests.test_mobile_parity_golden -v)

echo "PASS: NutriOffline mobile pack gate"
