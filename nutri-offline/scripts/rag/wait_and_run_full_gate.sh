#!/usr/bin/env bash
# Wait for scope=all index build, then run Phase 11 strict gate.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NUTRI="${ROOT}/nutri-offline"
META="${NUTRI}/indexes/nutri-foods/metadata.json"
BUILD_LOG="${1:-${NUTRI}/logs/build-index-all-*.log}"

echo "Waiting for full index build (metadata scope=all, build_in_progress=false)..."

while true; do
  if [[ -f "${META}" ]]; then
    scope="$(python3 -c "import json; m=json.load(open('${META}')); print(m.get('scope',''))")"
    in_progress="$(python3 -c "import json; m=json.load(open('${META}')); print(m.get('build_in_progress', False))")"
    records="$(python3 -c "import json; m=json.load(open('${META}')); print(m.get('record_count', 0))")"
    if [[ "${scope}" == "all" && "${in_progress}" != "True" && "${records}" -ge 2000000 ]]; then
      break
    fi
    echo "$(date -Iseconds) scope=${scope} records=${records} in_progress=${in_progress}"
  fi
  if compgen -G "${BUILD_LOG}" > /dev/null && grep -q "PASS: index v2 built" ${BUILD_LOG} 2>/dev/null; then
    break
  fi
  sleep 120
done

echo "Index build complete — running strict gate..."
exec "${ROOT}/scripts/validate-nutri-full-catalog.sh" full
