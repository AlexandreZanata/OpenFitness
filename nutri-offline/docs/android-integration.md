# Android integration guide — NutriOffline → OpenFitness

> **Status:** Draft for product decision · **No Kotlin code in v1**

## Goal

Bring the validated desktop pipeline (RAG + GGUF + llama.cpp) into OpenFitness as an **optional on-device nutrition assistant**, without cloud dependency.

## Validated desktop stack (Phase 7)

```
User question → bge-m3 embed (CPU) → LanceDB top-k
    → prompt with RAG context → llama-server (127.0.0.1:8080) → PT-BR answer
```

## Integration options

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| **llama.cpp JNI** | True on-device, no sidecar | APK +2 GB, RAM heavy | Flagship devices only |
| **Local foreground service** | Reuse GGUF from Phase 6 | Battery, process mgmt | Prototype path |
| **Bundled sqlite-vec + small model** | Single DB file | Still need model asset | Evaluate in spike |

**Recommendation:** Validate on desktop (done in Phase 7), then spike **llama.cpp Android** with Qwen2.5-3B q4_k_m or Gemma 2B q4 in a separate `nutri-offline/android-spike/` folder before touching `:app`.

## Size budget (estimates)

| Asset | Size |
|-------|------|
| GGUF q4_k_m (3B) | ~1.9 GB |
| LanceDB index (v1 scope) | ~441 MB |
| bge-m3 embeddings runtime | ~570 MB HF cache (or smaller e5 model) |
| **Total** | **~3 GB** (too large for base APK — use on-demand download) |

## Proposed module boundary

| Module | Responsibility |
|--------|----------------|
| `:domain` | `NutriQuery`, `NutriSource` value objects (future) |
| `:nutri-ml` (new) | JNI / llama.cpp bridge, index loader — **not in v1** |
| `:app` | UI entry point, calls local API or embedded engine |

Keep ML **outside** `:domain` until use cases are approved in `docs/use-cases/`.

## Hardware requirements (on-device)

| Tier | RAM | Storage | Expected UX |
|------|-----|---------|-------------|
| Flagship | ≥ 8 GB | ≥ 4 GB free | 3B q4, acceptable latency |
| Mid-range | 6 GB | ≥ 3 GB | 2B model or CPU-only |
| Low-end | < 6 GB | — | Not supported for local LLM v1 |

## Next steps (when product approves)

1. Spike llama.cpp Android with bundled q4_k_m
2. Evaluate sqlite-vec for index bundling (Phase 3 N-03-07 deferred)
3. Promote `UC-Nutri-Query` to `docs/use-cases/`
4. Define ABAC: nutrition queries read-only, no persistence without user confirm

## References

- [Phase 7 TASKS.md](../phases/07-app-integration/TASKS.md)
- [llama.cpp Android examples](https://github.com/ggml-org/llama.cpp/tree/master/examples/llama.android)
