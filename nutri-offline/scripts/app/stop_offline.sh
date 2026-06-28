#!/usr/bin/env bash
# Stop NutriOffline background services.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PID_DIR="${ROOT}/run"

stop_pidfile() {
    local name="$1"
    local file="${PID_DIR}/${name}.pid"
    if [[ -f "${file}" ]]; then
        local pid
        pid="$(cat "${file}")"
        if kill -0 "${pid}" 2>/dev/null; then
            kill "${pid}" 2>/dev/null || true
            wait "${pid}" 2>/dev/null || true
            echo "Stopped ${name} (pid ${pid})"
        fi
        rm -f "${file}"
    fi
}

stop_pidfile "nutri-app"
stop_pidfile "llama-server"

# Fallback: kill by command line
pkill -f "llama-server.*nutri-qwen25" 2>/dev/null || true

echo "PASS: NutriOffline services stopped"
