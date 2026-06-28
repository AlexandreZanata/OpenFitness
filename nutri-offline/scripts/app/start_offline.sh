#!/usr/bin/env bash
# Start NutriOffline stack: llama-server (+ optional FastAPI).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PID_DIR="${ROOT}/run"
LOG_DIR="${ROOT}/logs"
mkdir -p "${PID_DIR}" "${LOG_DIR}"

GGUF="$(find "${ROOT}/models/gguf" -name '*.gguf' -type f 2>/dev/null | head -1)"
if [[ -z "${GGUF}" ]]; then
    echo "ERROR: GGUF missing — run scripts/export/run_all.py"
    exit 1
fi

export HF_HOME="${ROOT}/models/base"
export NUTRI_GGUF="${GGUF}"

bash "${ROOT}/scripts/inference/build_llama_cpp.sh"

if [[ -f "${PID_DIR}/llama-server.pid" ]] && kill -0 "$(cat "${PID_DIR}/llama-server.pid")" 2>/dev/null; then
    echo "llama-server already running (pid $(cat "${PID_DIR}/llama-server.pid"))"
else
    bash "${ROOT}/scripts/inference/serve.sh" > "${LOG_DIR}/llama-server.log" 2>&1 &
    echo $! > "${PID_DIR}/llama-server.pid"
    echo "Started llama-server pid $(cat "${PID_DIR}/llama-server.pid")"
fi

# Wait for llama-server
for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:8080/health" >/dev/null 2>&1 || \
       curl -sf "http://127.0.0.1:8080/" >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

if [[ "${START_FASTAPI:-0}" == "1" ]] || [[ "${START_CHAT:-0}" == "1" ]]; then
    source "${ROOT}/venv/bin/activate"
    python "${ROOT}/scripts/app/server.py" > "${LOG_DIR}/nutri-app.log" 2>&1 &
    echo $! > "${PID_DIR}/nutri-app.pid"
    APP_PORT="${NUTRI_APP_PORT:-8090}"
    echo "Started FastAPI on 127.0.0.1:${APP_PORT} (pid $(cat "${PID_DIR}/nutri-app.pid"))"
    echo "Chat UI: http://127.0.0.1:${APP_PORT}/"
fi

cat <<EOF

NutriOffline is ready (offline).

CLI:
  cd ${ROOT} && source venv/bin/activate
  export HF_HOME="\$(pwd)/models/base"
  python scripts/app/nutri_cli.py ask "Quantas calorias tem arroz branco cozido?"
  python scripts/app/nutri_cli.py repl --debug

API / chat UI (optional):
  bash scripts/app/start_chat.sh
  # or: START_FASTAPI=1 bash scripts/app/start_offline.sh
  # open http://127.0.0.1:8090/
  curl -X POST http://127.0.0.1:8090/v1/nutri/ask -H 'Content-Type: application/json' \\
    -d '{"question":"Quantas calorias tem banana prata?"}'

Stop:
  bash scripts/app/stop_offline.sh
EOF
