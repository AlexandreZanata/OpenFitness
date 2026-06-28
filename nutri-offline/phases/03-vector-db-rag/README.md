# Phase 3 — Offline vector DB (RAG index)

> **Status:** Done (2026-06-27)  
> **Parent:** [Phase 2](../02-data-normalization/README.md)  
> **Goal:** Build a local semantic search index over normalized foods for runtime RAG retrieval.

---

## Objective

Index all normalized food records with multilingual embeddings. At runtime: user question → embedding → top-k relevant foods → inject as context into fine-tuned LLM prompt.

**RAG handles factual lookup. Fine-tuning handles reasoning and response format.**

---

## Architecture

```
foods.parquet
     ↓
build_index.py  →  text_for_embedding per record
     ↓
bge-m3 (sentence-transformers)  →  vector[1024]
     ↓
LanceDB / sqlite-vec  →  indexes/nutri-foods/
     ↓
query_rag.py  →  top-k + metadata (kcal, source, etc.)
```

---

## Vector DB decision

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **LanceDB** | Fast on large datasets, columnar, embedded | Extra dependency | **Primary choice** ✅ |
| **sqlite-vec** | Single `.db` file, minimal deps | Slower at very large scale | Good for app bundling (Phase 7) |
| ChromaDB | Simple Python API | Heavier, less ideal for millions | Fallback |
| FAISS | Fastest pure search | No rich metadata | Low-level index only |

**Decision:** LanceDB for build/query; sqlite-vec spike deferred to Phase 7 app bundling.

---

## Embedding model

| Model | Dimensions | PT-BR | VRAM |
|-------|------------|-------|------|
| **BAAI/bge-m3** | 1024 | Strong | ~2 GB GPU or CPU |
| intfloat/multilingual-e5-base | 768 | Good | Lighter |

**Primary:** `BAAI/bge-m3` via `sentence-transformers` (normalize_embeddings=True; no query prefix).

---

## Text for embedding (per record)

Template:

```
{name} | {category} | {brand} | Source: {source}
Nutrients per {serving_basis}: {energy_kcal} kcal, protein {protein_g}g, carbs {carbohydrate_g}g, fat {fat_g}g
Ingredients: {ingredients_text truncated to 500 chars}
```

Store full metadata alongside vector for RAG context injection.

---

## Index scope (v1)

Default `--scope v1` indexes **107,768** rows:

- All TACO (597)
- All OFF Brazil (32,996)
- FDC Foundation foods only (~74k)

Use `--scope all` for the full 2M+ catalog (slow; not required for v1).

---

## Query examples (acceptance)

| Query (PT-BR) | Expected behavior | Result |
|---------------|-------------------|--------|
| "comida rica em ferro" | Returns iron-rich foods (if micronutrient indexed) or semantically similar | ✅ |
| "substituto de leite sem lactose" | Returns lactose-free milk alternatives | ✅ |
| "quantas calorias tem arroz branco" | Returns arroz entries from TACO/OFF | ✅ (OFF ranks higher; TACO uses "tipo 1" naming) |
| "iogurte grego proteína" | Returns high-protein yogurt products | ✅ |

---

## Commands

```bash
cd nutri-offline
source venv/bin/activate
export HF_HOME="$(pwd)/models/base"

# Build index (v1 scope, ~16 min on RTX 4060)
python scripts/rag/run_all.py --scope v1 --device cuda

# Query only (skip rebuild)
python scripts/rag/run_all.py --skip-build

# Ad-hoc query
python scripts/rag/query_rag.py "quantas calorias tem arroz branco" --top-k 5

# Repo gate (from project root)
./scripts/validate-nutri-rag.sh
```

---

## Out of scope

| Item | Phase |
|------|-------|
| Hybrid BM25 + vector search | Future optimization |
| Fine-tuned embedding model | Out of scope for v1 |
| Full OFF global index | Brazil subset only for v1 |
| sqlite-vec prototype | Phase 7 app bundling |

---

## Definition of done

- [x] Embeddings generated for normalized food catalog
- [x] LanceDB index persisted to `indexes/nutri-foods/`
- [x] Query script returns top-5 relevant results for acceptance queries
- [x] Index build reproducible from `foods.parquet`
- [x] Query latency < 500ms on local hardware (CPU embedding acceptable) — **~60 ms warm**

---

**References:** [TASKS.md](TASKS.md) · [LanceDB docs](https://lancedb.github.io/lancedb/) · [bge-m3](https://huggingface.co/BAAI/bge-m3)
