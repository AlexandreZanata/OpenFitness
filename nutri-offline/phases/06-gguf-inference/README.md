# Phase 6 — GGUF export & local inference

> **Status:** Done (2026-06-28)  
> **Parent:** [Phase 5](../05-finetuning-training/README.md)  
> **Goal:** Export fine-tuned model to GGUF and serve inference via llama.cpp — no Python runtime required at inference time.

---

## Objective

Merge LoRA adapters (if needed), convert to GGUF with q4_k_m quantization, and validate inference on local hardware via llama.cpp server on localhost.

---

## Export pipeline

```
models/adapters/{adapter}/
        ↓
Unsloth save_pretrained_gguf (auto-merge)
        ↓
models/gguf/nutri-qwen25-3b-{adapter}-q4_k_m.gguf  (~1.9 GB)
        ↓
llama-server → http://127.0.0.1:8080/v1/chat/completions
```

**Current adapter:** `smoke-test` (Phase 0). Swap to `nutri-qwen25-3b-v1` after Phase 5.

---

## Quantization choice

| Quant | Size (3B est.) | Quality | Recommendation |
|-------|----------------|---------|----------------|
| q4_k_m | ~2 GB | Good balance | **Production default** ✅ |
| q5_k_m | ~2.5 GB | Better | If disk/VRAM allows |
| q8_0 | ~4 GB | Near full | Dev/debug only |

---

## Inference requirements

| Requirement | Target | Result |
|-------------|--------|--------|
| Runtime internet | None | ✅ localhost only |
| Server bind | 127.0.0.1 | ✅ |
| API format | OpenAI `/v1/chat/completions` | ✅ |
| Latency | < 30s full answer | ✅ ~12s max (CPU prebuild) |
| Context window | 4096 tokens | ✅ |

---

## Commands

```bash
cd nutri-offline
source venv/bin/activate
export HF_HOME="$(pwd)/models/base"
export NUTRI_ADAPTER=smoke-test   # or nutri-qwen25-3b-v1 after Phase 5

# Export GGUF (~16 min first run)
python scripts/export/run_all.py --skip-merge

# llama.cpp + inference tests
python scripts/inference/run_all.py --skip-export

# Repo gate (from project root)
./scripts/validate-nutri-inference.sh
```

---

## Prompt template (with RAG)

```
system: Você é um especialista em nutrição. Use APENAS o contexto abaixo...
Context:
[off] Arroz branco (100g): 344 kcal, ...
user: quantas calorias tem arroz branco
```

RAG + LLM validated: answer cites 340–344 kcal from context.

---

## Definition of done

- [x] GGUF file generated and loads in llama.cpp
- [x] Local server responds to chat completions API
- [x] Sample nutrition Q&A produces coherent PT-BR answer
- [x] RAG context injection tested manually
- [x] Model runs with WiFi disabled (localhost-only server)
- [x] Ready for [Phase 7](../07-app-integration/TASKS.md)

---

**References:** [TASKS.md](TASKS.md) · [llama.cpp](https://github.com/ggml-org/llama.cpp) · [Unsloth GGUF export](https://unsloth.ai/docs/basics/inference-and-deployment)
