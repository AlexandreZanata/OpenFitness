# Phase 3 tasks — Vector DB / RAG index

> **ID:** N-03 · Offline semantic search  
> **Quality gate:** Acceptance queries return relevant top-5; index rebuild reproducible  
> **Status:** Done (2026-06-27)  
> **Depends on:** [Phase 2](../02-data-normalization/TASKS.md)

---

## Owner decisions (resolve before N-03-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Vector DB** | LanceDB (recommended) · sqlite-vec · ChromaDB | ✅ LanceDB |
| **Embedding model** | bge-m3 (recommended) · multilingual-e5-base | ✅ BAAI/bge-m3 |
| **Embedding device** | GPU if VRAM free · CPU (recommended for build) | ✅ CUDA for build; CPU for query gate |
| **Index scope** | All normalized foods · TACO+FDC+OFF-BR · TACO+FDC only for v1 smoke | ✅ v1 scope (107,768 rows) |
| **Batch size** | 64 (CPU) · 128 · tune for VRAM | ✅ 64 |

---

## 0. Prerequisites

- [x] Phase 2 complete — `foods.parquet` validated
- [x] Read [README.md](README.md)
- [x] sentence-transformers installed (Phase 0)
- [x] LanceDB installed

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-03-01 | Text serialization for embedding | `scripts/rag/text_builder.py` | P0 | ✅ |
| N-03-02 | Embedding pipeline | `scripts/rag/embed.py` | P0 | ✅ |
| N-03-03 | LanceDB index build | `scripts/rag/build_index.py` | P0 | ✅ |
| N-03-04 | Query API | `scripts/rag/query_rag.py` | P0 | ✅ |
| N-03-05 | Acceptance test suite | `scripts/rag/test_queries.py` | P0 | ✅ |
| N-03-06 | Index metadata + versioning | `indexes/nutri-foods/metadata.json` | P1 | ✅ |
| N-03-07 | Evaluate sqlite-vec alternative | spike doc in README | P2 | ⏸ → [Phase 8](../08-mobile-pack/TASKS.md) N-08-04 |
| N-03-09 | Mobile index contract (Tier A/B/C) | `scripts/mobile/select_mobile_records.py` | P1 | ⬜ Phase 8 |

---

## 1. Text builder (N-03-01)

- [x] Function `build_embedding_text(record: FoodRecord) -> str`
- [x] Truncate ingredients to 500 chars
- [x] Handle null nutrients gracefully (omit field, don't write "None")
- [x] Unit test: TACO arroz record produces expected text shape
- [x] Batch builder reading from Parquet in chunks (10k rows)

---

## 2. Embedding pipeline (N-03-02)

- [x] Load `BAAI/bge-m3` via sentence-transformers
- [x] Batch encode with progress bar (tqdm)
- [x] Save intermediate: `data/processed/embeddings.npy` + row id mapping (optional — or embed directly to LanceDB)
- [x] Log: total records, embed time, device used
- [x] For bge-m3: prepend query instruction if required by model card
- [x] Memory-safe: process in chunks of 10k–50k records

---

## 3. LanceDB index (N-03-03)

- [x] Create table `foods` in `indexes/nutri-foods/`
- [x] Schema: `id`, `vector`, `name`, `source`, `energy_kcal`, `protein_g`, `carbohydrate_g`, `fat_g`, `embedding_text`, `rag_context` (formatted for LLM injection)
- [x] `rag_context` template:
  ```
  [{source}] {name} ({serving_basis}): {energy_kcal} kcal, P {protein_g}g, C {carbohydrate_g}g, G {fat_g}g
  ```
- [x] Build IVF/PQ index if dataset > 100k (follow LanceDB docs)
- [x] Verify index size on disk — log MB

---

## 4. Query API (N-03-04)

- [x] CLI: `python scripts/rag/query_rag.py "quantas calorias tem arroz branco" --top-k 5`
- [x] Function `search(query: str, top_k: int = 5) -> list[RagResult]`
- [x] `RagResult`: score, id, name, source, rag_context, metadata
- [x] Embed query with same model + instruction prefix
- [x] Return results sorted by cosine similarity

---

## 5. Acceptance tests (N-03-05)

- [x] Test queries from README acceptance table
- [x] Assert top-5 contains at least 1 arroz result (TACO or OFF) for arroz query
- [x] Assert lactose-free query returns dairy alternatives or explicit lactose-free products
- [x] Log precision@5 manually for 20 curated queries — target ≥ 80% relevant
- [x] Document failures for dataset/index improvement

**Results (2026-06-27):** 4/4 acceptance queries pass; max query latency 60 ms (warm embedder).

---

## 6. Index metadata (N-03-06)

- [x] `indexes/nutri-foods/metadata.json`:
  - embedding model name + revision
  - record count
  - build timestamp
  - source parquet checksum
  - lancedb version

**Build stats:** 107,768 records · 440.9 MB · 973 s (CUDA) · scope v1

---

## 7. sqlite-vec spike (N-03-07) — optional

- [ ] Prototype same data in sqlite-vec single file
- [ ] Compare query latency vs LanceDB
- [ ] Document recommendation for Phase 7 app bundling

Deferred to Phase 7 app bundling evaluation.

---

## Gate

- [x] All P0 tasks complete
- [x] Index rebuild from scratch in < 4 hours (estimate for full catalog)
- [x] Acceptance queries pass
- [x] Ready for [Phase 7](../07-app-integration/TASKS.md) RAG integration (can proceed in parallel with Phases 4–6)

**Effort estimate:** 5–7 days
