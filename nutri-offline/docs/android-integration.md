# Android integration guide — NutriOffline → OpenFitness

> **Status:** Updated for Phase 8 mobile pack · **No Kotlin code in v1**

## Goal

Bring validated nutrition assistant capabilities into OpenFitness as an **optional on-device module**, 100% offline, **≤200 MB** one-time download on common phones.

---

## Two runtimes

| Runtime | Phase | Pack | LLM | Target |
|---------|-------|------|-----|--------|
| **Desktop** | 7 | ~3 GB | Qwen2.5-3B GGUF | Dev / power users |
| **Mobile** | 8 | **≤200 MB** | None | OpenFitness `:app` |

Phase 8 achieves **capability parity** with desktop via lookup + rule engine — not by bundling the 3B model. See [MOBILE-CAPABILITY-MATRIX.md](MOBILE-CAPABILITY-MATRIX.md).

---

## Mobile pack layout (Phase 8)

```
nutri-mobile.pack (≤200 MB)
├── manifest.json          # version, checksums, record counts
├── embedder.onnx          # int8, ≤35 MB
├── vectors.db             # sqlite-vec int8, Tier A/B/C
└── lexicon.db             # FTS5 aliases + keywords
```

Load sequence on Android:

1. Verify checksum from `manifest.json`
2. mmap / open `vectors.db` read-only
3. Load ONNX embedder via ONNX Runtime Mobile
4. Route queries through shared intent taxonomy (port from `intent_parser.py`)

---

## Validated desktop stack (Phase 7 — reference only)

```
User question → bge-m3 embed → LanceDB top-k → llama-server → PT-BR answer
```

Mobile replaces LanceDB + bge-m3 with **sqlite-vec + ONNX small embedder**, and replaces llama-server with **reasoning_engine.py** logic (compare, substitute, templates).

---

## Integration options

| Approach | Pros | Cons | Phase 8 recommendation |
|----------|------|------|------------------------|
| **Embedded pack + Kotlin FFI to ONNX/sqlite** | True on-device, ≤200 MB | JNI work | **Primary path** |
| **Local foreground service (desktop server)** | Reuse Python | Battery, RAM, not 200 MB | Desktop only |
| **llama.cpp JNI + 3B GGUF** | Generative LLM | ~2 GB — **over budget** | Not in Phase 8 |

**Recommendation:** Implement Python reference runtime in Phase 8 (Blocks A–G), then spike **ONNX Runtime Mobile + sqlite** in `android-spike/` before touching `:app`.

---

## Size budget (Phase 8 — enforced)

| Asset | Max size |
|-------|----------|
| Full mobile pack | **200 MB** |
| Embedder ONNX int8 | 35 MB |
| Vector + metadata index | 135 MB |
| Lexicon + manifest | 10 MB |

No optional LLM download in v1. Future “expansion pack” for more OFF products is a **product decision** — must not break 200 MB base without explicit user consent.

---

## Hardware requirements (on-device)

| Tier | RAM | Storage | Phase 8 UX |
|------|-----|---------|------------|
| Mid-range | ≥6 GB | ≥500 MB free for pack | **Target** — lookup p95 ≤500 ms |
| Flagship | ≥8 GB | ≥500 MB | Same pack; headroom for app |
| Low-end | <6 GB | — | Not supported v1 |

---

## Proposed module boundary

| Module | Responsibility |
|--------|----------------|
| `:domain` | `NutriQuery`, `NutriSource` value objects (future) |
| `:nutri-ml` (new) | Pack loader, ONNX embed, sqlite-vec search, template renderer |
| `:app` | UI entry point; triggers download of `nutri-mobile.pack` |

Keep ML **outside** `:domain` until use cases are approved in `docs/use-cases/`.

---

## Phase 8 task cross-reference

| Task | Android impact |
|------|----------------|
| N-08-17 `build_pack.py` | Asset bundled or downloaded on first use |
| N-08-18 size gate | CI blocks APK/pack regression |
| N-08-19 parity benchmark | Acceptance before `:nutri-ml` JNI |
| N-08-20 | This doc + spike folder |

Full checklist: [phases/08-mobile-pack/TASKS.md](../phases/08-mobile-pack/TASKS.md)

---

## Next steps

1. Complete Phase 8 Blocks A–G in Python (parity proof)
2. Spike ONNX Runtime Mobile + sqlite-vec read in `android-spike/`
3. Promote `UC-Nutri-Query` to `docs/use-cases/`
4. Define ABAC: nutrition queries read-only, no persistence without user confirm

---

## References

- [Phase 8 README](../phases/08-mobile-pack/README.md)
- [MOBILE-CAPABILITY-MATRIX.md](MOBILE-CAPABILITY-MATRIX.md)
- [Phase 7 TASKS.md](../phases/07-app-integration/TASKS.md)
- [llama.cpp Android examples](https://github.com/ggml-org/llama.cpp/tree/master/examples/llama.android) — desktop/flagship LLM path only
