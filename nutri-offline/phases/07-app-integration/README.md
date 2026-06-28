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

# FastAPI (optional)
pip install fastapi uvicorn
START_FASTAPI=1 bash scripts/app/start_offline.sh
curl -X POST http://127.0.0.1:8090/v1/nutri/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Quantas calorias tem arroz branco?","debug":true}'

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
GET  /v1/nutri/health
```

Bind `127.0.0.1:8090` only. llama-server on `:8080`.

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
