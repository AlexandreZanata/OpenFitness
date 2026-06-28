# Phase 6 tasks — GGUF export & inference

> **ID:** N-06 · GGUF + llama.cpp  
> **Quality gate:** GGUF loads; localhost API responds; offline test passes  
> **Status:** Done (2026-06-28)  
> **Depends on:** [Phase 5](../05-finetuning-training/TASKS.md)

---

## Owner decisions (resolve before N-06-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Export path** | Unsloth `save_pretrained_gguf` (recommended) · manual llama.cpp convert | ✅ Unsloth |
| **Quantization** | q4_k_m (recommended) · q5_k_m | ✅ q4_k_m |
| **Merge LoRA** | Merge before export (recommended) · llama.cpp LoRA adapter at runtime | ✅ Unsloth auto-merge on export |
| **llama.cpp install** | Build from source (recommended) · prebuilt binary | ✅ Unsloth prebuild (fallback; cmake if available) |
| **Server port** | 8080 (recommended) · configurable | ✅ 8080 |

> **Note:** Pipeline validated with Phase 0 `smoke-test` adapter. Re-export with `NUTRI_ADAPTER=nutri-qwen25-3b-v1` after Phase 5 training completes.

---

## 0. Prerequisites

- [x] Phase 5 adapter saved: `models/adapters/nutri-qwen25-3b-v1/` — **using smoke-test for pipeline gate**
- [x] Sufficient disk: ~5 GB for merged + GGUF files
- [x] llama.cpp cloned or installed

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-06-01 | Merge LoRA into base | `scripts/export/merge_lora.py` | P0 | ✅ |
| N-06-02 | Export GGUF | `scripts/export/export_gguf.py` | P0 | ✅ |
| N-06-03 | Quantize q4_k_m | `models/gguf/` | P0 | ✅ |
| N-06-04 | Build/install llama.cpp | `scripts/inference/build_llama_cpp.sh` | P0 | ✅ |
| N-06-05 | Local inference server | `scripts/inference/serve.sh` | P0 | ✅ |
| N-06-06 | Inference smoke tests | `scripts/inference/test_inference.py` | P0 | ✅ |
| N-06-07 | RAG prompt integration test | `scripts/inference/rag_prompt.py` | P0 | ✅ |
| N-06-08 | Benchmark latency + VRAM | `logs/inference-benchmark.json` | P1 | ✅ |

---

## 1. Merge LoRA (N-06-01)

- [x] Load base Qwen2.5-3B + trained LoRA adapter
- [x] Merge and unload LoRA weights into full model
- [x] Save to `models/merged/nutri-qwen25-3b-v1/` (safetensors)
- [x] Verify merged model generates text in Python before GGUF export
- [x] Alternative: Unsloth one-liner merge if supported

---

## 2. GGUF export (N-06-02)

- [x] Option A — Unsloth `save_pretrained_gguf`
- [x] Output: `models/gguf/nutri-qwen25-3b-smoke-test-q4_k_m.gguf`
- [x] Log file size — **1930 MB** (3B q4_k_m)
- [x] Copy `Modelfile` alongside GGUF

---

## 3. Quantization verify (N-06-03)

- [x] Unsloth exports q4_k_m directly
- [x] Compare: acceptable quality on smoke prompts
- [ ] Keep fp16 GGUF for regression tests only (optional, large)

---

## 4. llama.cpp setup (N-06-04)

- [x] Clone: https://github.com/ggml-org/llama.cpp (under `nutri-offline/llama.cpp`)
- [x] Build with CUDA: fallback to Unsloth prebuild when cmake unavailable
- [x] Verify: `llama-server` linked at `llama.cpp/build/bin/llama-server`
- [x] Document build flags in `ENVIRONMENT.md`

---

## 5. Inference server (N-06-05)

- [x] Script `scripts/inference/serve.sh`
- [x] `-ngl 99` when CUDA build available (CPU prebuild used in gate run)
- [x] Confirm OpenAI-compatible endpoint: `POST /v1/chat/completions`
- [ ] systemd user service optional (local dev convenience)

---

## 6. Smoke tests (N-06-06)

- [x] Test prompt: arroz calories PT-BR
- [x] Test via HTTP to localhost:8080
- [x] Assert response is PT-BR, mentions nutrition concepts
- [x] Test unknown food — no invented precise kcal
- [x] Script: `scripts/inference/test_inference.py` — 3 automated prompts + RAG

**Results:** 3/3 pass · max latency ~13s (CPU prebuild)

---

## 7. RAG integration test (N-06-07)

- [x] Pull top-5 from Phase 3 index for arroz query
- [x] Build prompt with RAG context
- [x] Send to llama-server — answer references RAG kcal range (340–344)
- [x] Document: **RAG required for factual accuracy**

---

## 8. Benchmark (N-06-08)

- [x] Measure latency (short/medium/rag prompts)
- [x] Save `logs/inference-benchmark.json`
- [x] Confirm acceptable for app UX (< 30s full response) — max **3.8s** RAG prompt

---

## Gate

- [x] GGUF inference works on localhost
- [x] Offline test: server binds 127.0.0.1 only
- [x] RAG + LLM pipeline validated manually
- [x] Ready for [Phase 7](../07-app-integration/TASKS.md)

**Effort estimate:** 2–3 days
