#!/usr/bin/env bash
# Start NutriOffline stack + browser chat UI (llama-server + FastAPI).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${NUTRI_APP_PORT:-8090}"

START_FASTAPI=1 bash "${ROOT}/scripts/app/start_offline.sh"

echo ""
echo "Chat UI: http://127.0.0.1:${PORT}/"
echo "API docs: http://127.0.0.1:${PORT}/docs"
echo ""
echo "Stop: bash scripts/app/stop_offline.sh"
