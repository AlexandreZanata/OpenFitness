# Phase 7 tasks — App integration

> **ID:** N-07 · End-to-end offline assistant  
> **Quality gate:** 5 acceptance scenarios pass in airplane mode  
> **Status:** Done (2026-06-28)  
> **Depends on:** [Phase 3](../03-vector-db-rag/TASKS.md), [Phase 6](../06-gguf-inference/TASKS.md)

---

## Owner decisions (resolve before N-07-01)

| Decision | Options | Status |
|----------|---------|--------|
| **v1 UI** | CLI only (recommended) · FastAPI + simple web · Tauri desktop | ✅ CLI + FastAPI |
| **Vector DB at runtime** | LanceDB (recommended) · sqlite-vec single file | ✅ LanceDB |
| **Embedding at runtime** | CPU bge-m3 (recommended) · GPU if idle | ✅ CPU |
| **top_k default** | 5 (recommended) · 3 · 10 | ✅ 5 |
| **OpenFitness Android** | Document only · spike in `.local` | ✅ Document only |

---

## 0. Prerequisites

- [x] Phase 3 index built and queryable
- [x] Phase 6 GGUF server running on localhost:8080
- [x] Phase 5 fine-tuned model deployed — **smoke-test adapter used; swap after Phase 5**

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-07-01 | RAG orchestrator module | `scripts/app/rag_pipeline.py` | P0 | ✅ |
| N-07-02 | LLM client (llama.cpp) | `scripts/app/llm_client.py` | P0 | ✅ |
| N-07-03 | Prompt builder | `scripts/app/prompt_builder.py` | P0 | ✅ |
| N-07-04 | CLI interface | `scripts/app/nutri_cli.py` | P0 | ✅ |
| N-07-05 | FastAPI local server | `scripts/app/server.py` | P1 | ✅ |
| N-07-06 | Acceptance test suite | `scripts/app/test_offline_e2e.py` | P0 | ✅ |
| N-07-07 | Startup orchestration | `scripts/app/start_offline.sh` | P1 | ✅ |
| N-07-08 | Android integration guide | `docs/android-integration.md` | P1 | ✅ |
| N-07-09 | OpenFitness use case draft | `docs/UC-nutri-query.md` | P2 | ✅ |
| N-07-10 | Mobile runtime adapter | `scripts/mobile/mobile_assistant.py` | P1 | ⬜ [Phase 8](../08-mobile-pack/TASKS.md) N-08-16 |

---

## 1. RAG orchestrator (N-07-01)

- [x] Class `RagPipeline` with embed, search, build_context
- [x] Load LanceDB index from `indexes/nutri-foods/`
- [x] Load bge-m3 once at startup (singleton)
- [x] Unit test: arroz query returns results in top-5

---

## 2. LLM client (N-07-02)

- [x] HTTP client for `http://127.0.0.1:8080/v1/chat/completions`
- [x] Timeout handling, connection refused → clear error
- [x] No fallback to cloud API — offline only

---

## 3. Prompt builder (N-07-03)

- [x] System message: role + RAG context + citation rules
- [x] Max context budget: truncate RAG to ~3500 tokens
- [x] Debug mode logs prompt token estimate

---

## 4. CLI (N-07-04)

- [x] `nutri_cli.py ask "..."`
- [x] Flags: `--top-k`, `--debug`, `--no-rag`, `--json`
- [x] REPL mode: `nutri_cli.py repl`

---

## 5. FastAPI server (N-07-05)

- [x] `POST /v1/nutri/ask` per README API design
- [x] `GET /v1/nutri/health`
- [x] Bind 127.0.0.1 only (port 8090)

---

## 6. Acceptance tests (N-07-06)

- [x] All 5 scenarios from README
- [x] Offline guard blocks external URLs
- [x] Report: `logs/e2e-offline-{timestamp}.json`

**Result:** 5/5 pass · max scenario latency ~23s

---

## 7. Startup script (N-07-07)

- [x] `start_offline.sh` — GGUF check, llama-server, usage hints
- [x] `stop_offline.sh` — kill background processes

---

## 8. Android integration guide (N-07-08)

- [x] Options, size budget, module boundary documented

---

## 9. Use case draft (N-07-09)

- [x] `UC-Nutri-Query` in GIVEN/WHEN/THEN format

---

## Gate

- [x] All P0 tasks complete
- [x] 5/5 acceptance scenarios pass offline
- [x] CLI transcript + E2E JSON log
- [x] **NutriOffline pipeline complete** (Phase 5 training remains for production model quality)

---

## Project completion checklist

- [x] [Phase 0](../00-hardware-environment/TASKS.md) — environment
- [x] [Phase 1](../01-data-acquisition/TASKS.md) — raw data
- [x] [Phase 2](../02-data-normalization/TASKS.md) — unified schema
- [x] [Phase 3](../03-vector-db-rag/TASKS.md) — vector index
- [x] [Phase 4](../04-finetuning-dataset/TASKS.md) — training dataset
- [x] [Phase 5](../05-finetuning-training/TASKS.md) — QLoRA fine-tuning (adapter v1)
- [x] [Phase 6](../06-gguf-inference/TASKS.md) — GGUF inference
- [x] [Phase 7](TASKS.md) — app integration (desktop)
- [ ] [Phase 8](../08-mobile-pack/TASKS.md) — mobile pack ≤200 MB

**Effort estimate:** 2–3 weeks
