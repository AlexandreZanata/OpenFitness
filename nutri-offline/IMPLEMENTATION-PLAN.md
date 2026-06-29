# Implementation plan — NutriOffline

> In-repo pipeline (`nutri-offline/`; artifacts gitignored). Real fine-tuning + offline vector RAG for nutrition.
> **Rules:** (1) every data source cites an official URL; (2) QLoRA only (no full fine-tuning on 8 GB VRAM); (3) RAG for factual lookup, fine-tuning for domain tone and reasoning.

---

## Goal

Train a **small LLM specialist in nutrition and food composition** that runs **100% offline** at runtime, combined with a local vector search index over TACO, FoodData Central, and Open Food Facts.

```
User question → local embedding → vector DB (top-k)
                                      ↓
              fine-tuned LLM (GGUF, llama.cpp) → natural-language answer
```

| Component | Technology |
|-----------|------------|
| Base model | Qwen2.5-3B-Instruct (primary) · Qwen3-4B / Llama 3.2 3B (alternatives) |
| Fine-tuning | Unsloth + PEFT + TRL + bitsandbytes (QLoRA 4-bit NF4) |
| Inference | llama.cpp / GGUF (q4_k_m) |
| Vector DB | LanceDB or sqlite-vec (embedded, no server) |
| Embeddings | BAAI/bge-m3 or intfloat/multilingual-e5 |
| Data processing | DuckDB, Python scripts |
| Hardware | RTX 4060 8 GB — batch size 1–2, fp16, avoid bf16 |

**Why fine-tuning + RAG (not either alone):**

- Fine-tuning alone cannot memorize 600k+ food rows with numeric fidelity — it will hallucinate macros.
- RAG alone does not teach Brazilian nutrition terminology, portion reasoning, or response format.
- Combined approach is the realistic state of the art for domain apps.

---

## Phase order

| Phase | Module | Est. duration | Depends on |
|-------|--------|---------------|------------|
| **0** | [Hardware & environment](phases/00-hardware-environment/README.md) | 1–2 days | — |
| **1** | [Data acquisition](phases/01-data-acquisition/README.md) | 3–5 days | Phase 0 |
| **2** | [Data normalization](phases/02-data-normalization/README.md) | 5–7 days | Phase 1 |
| **3** | [Vector DB / RAG](phases/03-vector-db-rag/README.md) | 5–7 days | Phase 2 |
| **4** | [Fine-tuning dataset](phases/04-finetuning-dataset/README.md) | 7–10 days | Phase 2 |
| **5** | [Fine-tuning training](phases/05-finetuning-training/README.md) | 2–5 days exec + iteration | Phase 4 |
| **6** | [GGUF inference](phases/06-gguf-inference/README.md) | 2–3 days | Phase 5 |
| **7** | [App integration](phases/07-app-integration/README.md) | 2–3 weeks | Phases 3, 6 |
| **8** | [Mobile pack ≤200 MB](phases/08-mobile-pack/README.md) | 4–6 weeks | Phases 3, 7, RAG V2 |
| **9** | [Semantic engine v2](phases/09-semantic-engine/README.md) | 3–4 weeks | Phase 8 |
| **10** | [Mobile QA benchmark B20](phases/10-mobile-qa/README.md) | 3–4 days | Phase 9 |
| **11** | [Full catalog index](phases/11-full-catalog-index/README.md) | 3–5 days + overnight build | Phases 2, 3, 5, 7 |

**Total estimate:** 8–14 weeks part-time (Phases 0–7 desktop + Phases 8–11 mobile + full catalog).

---

## Training configuration (starting point)

```
method:              QLoRA (4-bit NF4)
base model:          Qwen2.5-3B-Instruct
rank (r):            16
alpha:               16–32
target_modules:      all-linear (attention + MLP)
batch_size:          1–2
grad_accum_steps:    4–8
learning_rate:       2e-4
epochs:              2–3
max_sequence:        1024–2048 tokens
optimizer:           paged_adamw_8bit
precision:           fp16 (avoid bf16 on RTX 4060)
export:              GGUF q4_k_m
```

---

## Dataset targets

| Metric | Target |
|--------|--------|
| Fine-tuning examples | 2,000–5,000 high-quality Q&A pairs |
| Format | ChatML JSONL (`messages`: system / user / assistant) |
| Split | 90% train / 10% validation |
| Language | Brazilian Portuguese (primary) |
| Content | Macros, comparisons, substitutions, allergens, portion math |

---

## Data sources (official)

| Source | Coverage | License |
|--------|----------|---------|
| [TACO / NEPA-UNICAMP](https://www.nepa.unicamp.br/taco/index.php) | ~600 Brazilian foods | Public academic research — cite NEPA/UNICAMP |
| [TBCA / USP](https://www.tbca.net.br/) | Complementary BR foods + biodiversity | Academic — cite USP |
| [FoodData Central / USDA](https://fdc.nal.usda.gov/) | ~400k records (Foundation + Branded) | CC0 1.0 |
| [Open Food Facts](https://world.openfoodfacts.org/data) | ~3.7M global products | ODbL — attribution required |

Details: [phases/01-data-acquisition/OFFICIAL-REFERENCE.md](phases/01-data-acquisition/OFFICIAL-REFERENCE.md)

---

## Realistic expectations

| Expectation | Reality |
|-------------|---------|
| Model "knows everything by heart" | No — 3–4B fine-tuned model excels at format, reasoning, terminology; exact numbers come from RAG |
| Training time per epoch | 1–4 hours on RTX 4060 8 GB (3B model, 2k–5k examples) |
| 7–8B models | Viable at VRAM limit — batch size 1, shorter sequences, slower |
| Dataset quality | 2,000 curated examples > 20,000 noisy ones |

---

## Definition of done (full pipeline)

- [ ] All four data sources downloaded, normalized, validated in DuckDB
- [ ] Vector index built with bge-m3; semantic search returns relevant foods in PT-BR
- [ ] 2,000+ ChatML examples; manual quality review on 10% sample
- [ ] QLoRA fine-tune completes without OOM; validation loss stable
- [ ] GGUF model runs via llama.cpp on localhost with no internet
- [ ] RAG pipeline: question → embedding → top-k → prompt → answer
- [ ] End-to-end offline test: airplane mode, factual macro answer with source citation
- [ ] **Phase 8:** Mobile pack ≤200 MB with desktop capability parity (lookup + rule-based reasoning)
- [ ] **Phase 9:** Semantic engine v2 — typo/ontology/portion normalization before vector search
- [ ] **Phase 10:** Mobile QA B20 — 100% R10 + B20
- [ ] **Phase 11:** Full catalog LanceDB index (`scope=all`) + four-layer benchmark gate

---

## Mobile vs desktop (Phase 8)

| Runtime | Pack size | LLM | Use case |
|---------|-----------|-----|----------|
| **Desktop** (Phases 6–7) | ~3 GB | Qwen2.5-3B GGUF | Dev, full catalog, optional LLM reasoning |
| **Mobile** (Phase 8) | **≤200 MB** | None on-device | OpenFitness Android, mid-range phones |

Mobile achieves parity via **expanded intent parser + hybrid RAG + rule engine** — not by compressing the 3B model. See [phases/08-mobile-pack/README.md](phases/08-mobile-pack/README.md).

**Phase 9** improves retrieval quality with a normalization-first semantic engine (spell-fix, synonyms, ontology, multi-surface vectors). See [phases/09-semantic-engine/README.md](phases/09-semantic-engine/README.md) and [docs/SEMANTIC-ENGINE-V2.md](docs/SEMANTIC-ENGINE-V2.md).

**Phase 11** indexes the full `foods.parquet` catalog (~2M rows) for desktop RAG and adds G-COV/G-RET/G-DOM/G-PERF benchmarks. See [phases/11-full-catalog-index/README.md](phases/11-full-catalog-index/README.md) and [docs/FULL-CATALOG-INDEX.md](docs/FULL-CATALOG-INDEX.md).

**References:** [README.md](README.md) · [Unsloth docs](https://unsloth.ai/docs) · [LanceDB](https://lancedb.github.io/lancedb/) · [llama.cpp](https://github.com/ggml-org/llama.cpp)
