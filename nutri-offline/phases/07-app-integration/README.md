# Phase 7 — Offline app integration (RAG + LLM)

> **Status:** Done (2026-06-28)  
> **Parent:** [Phase 3](../03-vector-db-rag/README.md) · [Phase 6](../06-gguf-inference/README.md)  
> **Goal:** Wire vector search + fine-tuned LLM into a 100% offline nutrition assistant — desktop prototype first, OpenFitness Android path documented.

---

## Objective

End-to-end offline pipeline validated:

```
User question (PT-BR)
    → embed query (bge-m3)
    → vector search (top-k foods)
    → build prompt with RAG context
    → llama.cpp localhost API
    → formatted answer with source citation
```

---

## Commands

```bash
cd nutri-offline
source venv/bin/activate
export HF_HOME="$(pwd)/models/base"

# Start stack (llama-server)
bash scripts/app/start_offline.sh

# CLI
python scripts/app/nutri_cli.py ask "Quantas calorias tem banana prata?" --debug
python scripts/app/nutri_cli.py repl

# Chat UI + API (optional)
bash scripts/app/start_chat.sh
# Runtime: desktop (LLM + LanceDB) | mobile pack (rule engine)

# Admin ↔ mobile mode parity (FastAPI must be running)
python scripts/app/test_admin_mobile_parity.py
python scripts/app/test_mobile_chat_api.py --runtime mobile
python scripts/app/test_mobile_chat_api.py --runtime desktop

# E2E acceptance
python scripts/app/test_offline_e2e.py

# Repo gate
./scripts/validate-nutri-app.sh

# Stop
bash scripts/app/stop_offline.sh
```

---

## Local API

```
POST /v1/nutri/ask
POST /v1/nutri/chat
POST /v1/nutri/chat/stream
GET  /v1/nutri/health?runtime=desktop|mobile
GET  /                        → chat UI
```

Request body accepts `"runtime": "desktop" | "mobile"` (default `desktop`).

Bind `127.0.0.1:8090` only. llama-server on `:8080`.

### HTTP 429 (Too Many Requests) on desktop

llama-server rejects concurrent requests when all inference **slots** are busy (default was effectively single-slot). Mitigations in this repo:

| Control | Default | Purpose |
|---------|---------|---------|
| `NUTRI_LLM_PARALLEL` | `4` | `--parallel` slots in `scripts/inference/serve.sh` |
| Health probe | GET `/health` only | No chat `ping` fallback while streaming (avoids slot contention) |
| Chat UI poll | 30s, skipped while busy | Reduces background load during generation |

Restart llama-server after changing `NUTRI_LLM_PARALLEL`.

---

## Acceptance scenarios (offline)

| # | Scenario | Result |
|---|----------|--------|
| 1 | TACO food calories | ✅ PASS |
| 2 | Compare two foods | ✅ PASS |
| 3 | Branded OFF product | ✅ PASS |
| 4 | Unknown food name | ✅ PASS |
| 5 | Session follow-up | ✅ PASS |

Report: `logs/e2e-offline-*.json`

---

## Android path

See [android-integration.md](../../nutri-offline/docs/android-integration.md) — document only for v1.

Use case draft: [UC-nutri-query.md](../../nutri-offline/docs/UC-nutri-query.md)

---

## Definition of done

- [x] CLI or API answers nutrition questions offline
- [x] RAG context visible in debug mode
- [x] All 5 acceptance scenarios pass in airplane mode (offline URL guard)
- [x] Integration guide written for future OpenFitness module
- [x] End-to-end latency documented (~5–23s per query, CPU llama prebuild)

---

**References:** [TASKS.md](TASKS.md) · [OpenFitness architecture](../../docs/architecture/overview.md)
