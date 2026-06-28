# UC-Nutri-Query — Ask nutrition question (offline)

> **Status:** Draft · [nutri-offline/docs/](.)  
> **Promote to** `docs/use-cases/` when product approves Android integration.

## Actor

OpenFitness user (or CLI/API consumer in NutriOffline prototype)

## Preconditions

- Fine-tuned GGUF model available locally (`models/gguf/`)
- LanceDB food index built (`indexes/nutri-foods/`)
- llama-server running on `127.0.0.1:8080` (or embedded engine on Android spike)
- No network required at runtime

## Main flow

1. User submits a nutrition question in PT-BR (full sentence) **or shorthand** (`arroz 100g`, `arroz 100g, carne 200g`).
2. **Lookup path (RAG V2):** if shorthand portion syntax is detected, system parses items, retrieves per-item from LanceDB with source boost, renders a grounded markdown table — **no LLM** (~65–150 ms).
3. **Reasoning path:** system embeds the question with bge-m3, retrieves top-k with compact table context, sends prompt to local LLM (llama.cpp).
4. System returns answer with source list, `mode` (`lookup` | `llm`), and optional debug RAG context.

## Alternative flows

| Condition | Behavior |
|-----------|----------|
| Shorthand portion lookup (`arroz 100g`) | Deterministic table from indexed records (BR-RET-002) |
| Food not in index | Lookup table row shows **Não encontrado** — no invented macros (BR-DS-002) |
| Branded product hint (`iogurte vigor`) | OFF-preferring retrieval |
| llama-server down | Lookup path still works; reasoning path returns clear error |
| Question in English | Supported minority; PT-BR primary |

## Applied rules

- **BR-DS-001:** Numeric answers trace to RAG context records
- **BR-DS-002:** No invented nutrients absent from context
- **BR-DS-004:** Consistent system prompt across requests
- **BR-RET-001:** Generic BR foods prefer TACO/TBCA when scores are close
- **BR-RET-002:** Lookup table macros come from `scale_nutrient()` only
- **BR-RET-003:** Multi-item queries retrieved independently; totals in Python

## Events raised

None persisted in v1 (read-only query surface).

## Acceptance criteria (Phase 7)

- [x] 5 offline scenarios pass (see `scripts/app/test_offline_e2e.py`)
- [x] CLI and FastAPI expose same orchestrator
- [x] End-to-end latency documented in E2E report

## API contract (local)

```
POST /v1/nutri/ask
{ "question": string, "top_k": int, "language": "pt-BR", "debug": bool, "mode": "auto"|"lookup"|"llm" }

Response includes: answer, sources, mode, latency_ms, model
```

See [Phase 7 README](../../phases/07-app-integration/README.md).
