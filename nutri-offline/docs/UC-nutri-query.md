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

1. User submits a nutrition question in PT-BR (e.g. calories, comparison, branded product).
2. System embeds the question with bge-m3.
3. System retrieves top-k food records from LanceDB.
4. System builds a chat prompt with RAG context and citation rules.
5. System sends prompt to local LLM (llama.cpp).
6. System returns answer with source list and optional debug RAG context.

## Alternative flows

| Condition | Behavior |
|-----------|----------|
| Food not in index | Answer states data not found — no invented macros (BR-DS-002) |
| llama-server down | Clear error: start offline stack |
| Question in English | Supported minority; PT-BR primary |

## Applied rules

- **BR-DS-001:** Numeric answers trace to RAG context records
- **BR-DS-002:** No invented nutrients absent from context
- **BR-DS-004:** Consistent system prompt across requests

## Events raised

None persisted in v1 (read-only query surface).

## Acceptance criteria (Phase 7)

- [x] 5 offline scenarios pass (see `scripts/app/test_offline_e2e.py`)
- [x] CLI and FastAPI expose same orchestrator
- [x] End-to-end latency documented in E2E report

## API contract (local)

```
POST /v1/nutri/ask
{ "question": string, "top_k": int, "language": "pt-BR", "debug": bool }
```

See [Phase 7 README](../../phases/07-app-integration/README.md).
