# Phase 8 tasks — Mobile pack (≤200 MB)

> **ID:** N-08 · Mobile capability parity  
> **Quality gate:** `nutri-mobile.pack` ≤200 MB; G1–G5 + NL parity set pass  
> **Status:** ✅ Blocks A–G complete (Block H Android JNI spike optional)  
> **Depends on:** [Phase 3](../03-vector-db-rag/TASKS.md) (data), [RAG V2 Phase B/C](../../docs/README-RAG-V2.md) (lookup path)

---

## Owner decisions (resolve before N-08-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Pack budget** | Hard 200 MB total | ✅ Locked |
| **On-device LLM** | None in v1 pack | ✅ Recommended — use rule engine |
| **Embedder** | bge-small-en-v1.5 int8 ONNX · multilingual-e5-small | ✅ bge-small-en-v1.5 (33.8 MB ONNX) |
| **Index runtime** | sqlite-vec (recommended) · bundled LanceDB lite | ✅ sqlite-vec + pysqlite3 |
| **OFF tier C size** | 5k · 8k · 10k products | ✅ 8k (8,597 total records) |
| **Android v1** | Python parity runtime first · JNI spike parallel | ✅ Python runtime done; JNI in Block H |

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [A — Specification](#block-a--specification) | Capability matrix + budget | ✅ |
| [B — Mobile index](#block-b--mobile-index) | sqlite-vec int8 build | ✅ |
| [C — Tiny embedder](#block-c--tiny-embedder) | ONNX export ≤35 MB | ✅ |
| [D — Intent expansion](#block-d--intent-expansion) | NL → lookup/compare/substitute | ✅ |
| [E — Rule engine](#block-e--rule-engine) | Replace LLM reasoning | ✅ |
| [F — Pack builder](#block-f--pack-builder) | Single artifact + size gate | ✅ |
| [G — Parity validation](#block-g--parity-validation) | vs desktop golden set | ✅ |
| [H — Android spike](#block-h--android-spike) | OpenFitness integration path | ⬜ optional |

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-08-01 | Capability matrix doc | `docs/MOBILE-CAPABILITY-MATRIX.md` | P0 | ✅ |
| N-08-02 | Budget spec + manifest schema | `scripts/mobile/pack_schema.json`, `pack_budget.py` | P0 | ✅ |
| N-08-03 | Record tier selector (A/B/C) | `scripts/mobile/select_mobile_records.py` | P0 | ✅ |
| N-08-04 | sqlite-vec index spike | `scripts/mobile/spike_sqlite_vec.py` | P0 | ✅ |
| N-08-05 | Mobile index builder | `scripts/mobile/build_mobile_index.py` | P0 | ✅ |
| N-08-06 | int8 vector quantization | inside `build_mobile_index.py` | P0 | ✅ |
| N-08-07 | Compact FTS + alias sqlite | `scripts/mobile/build_mobile_lexicon.py` | P0 | ✅ |
| N-08-08 | Mobile hybrid search port | `scripts/mobile/mobile_search.py` | P0 | ✅ |
| N-08-09 | Export embedder ONNX | `scripts/mobile/export_embedder_onnx.py` | P0 | ✅ |
| N-08-10 | Embedder A/B on mobile golden | extend `embedder_benchmark.py` | P1 | ⬜ deferred |
| N-08-11 | Intent parser NL expansion | extend `intent_parser.py` | P0 | ✅ |
| N-08-12 | Compare intent + patterns | `scripts/mobile/intents_compare.py` | P0 | ✅ |
| N-08-13 | Substitute intent + patterns | `scripts/mobile/intents_substitute.py` | P0 | ✅ |
| N-08-14 | Reasoning engine | `scripts/mobile/reasoning_engine.py` | P0 | ✅ |
| N-08-15 | NL response templates | `scripts/mobile/response_templates.py` | P0 | ✅ |
| N-08-16 | Mobile orchestrator | `scripts/mobile/mobile_assistant.py` | P0 | ✅ |
| N-08-17 | Pack builder | `scripts/mobile/build_pack.py` | P0 | ✅ |
| N-08-18 | Size gate script | `scripts/validate-nutri-mobile-pack.sh` | P0 | ✅ |
| N-08-19 | Parity benchmark | `scripts/mobile/benchmark_mobile_parity.py` | P0 | ✅ |
| N-08-20 | Android integration update | `docs/android-integration.md` | P1 | ✅ |
| N-08-21 | Unit tests — intent NL | `tests/test_mobile_intent.py` | P0 | ✅ |
| N-08-22 | Unit tests — reasoning | `tests/test_mobile_reasoning.py` | P0 | ✅ |
| N-08-23 | Golden parity tests | `tests/test_mobile_parity_golden.py` | P0 | ✅ |
| N-08-24 | CLI mobile mode | `nutri_cli.py ask --runtime mobile` | P1 | ✅ |
| N-08-25 | Phase cross-links | IMPLEMENTATION-PLAN, RAG V2, Phases 3/6/7 | P1 | ✅ |

---

## Block A — Specification

### N-08-01 Capability matrix

- [x] Map each desktop E2E scenario (S1–S5, G1–G5) to mobile implementation path
- [x] Classify: lookup | compare | substitute | clarify | unsupported
- [x] Document BR-RET-001/002/003 applicability on mobile
- [x] Publish `docs/MOBILE-CAPABILITY-MATRIX.md`

### N-08-02 Budget spec

- [x] Define `pack.manifest.json`: version, record counts, embedder id, checksums, size_bytes
- [x] Per-component size limits (see README budget table)
- [x] Fail build if any component exceeds allocation (`pack_budget.py`)

---

## Block B — Mobile index

### N-08-03 Record tier selector

- [x] Tier A: all TACO rows from `foods.parquet`
- [x] Tier B: all TBCA rows (0 in current v1 dataset)
- [x] Tier C: top N OFF products — rank by BR priority brands + macro completeness
- [x] Output: `data/processed/mobile_record_ids.parquet`
- [x] Log excluded count vs desktop v1 (33,593 scope → 8,597 selected)

### N-08-04 sqlite-vec spike

- [x] Prove vector search works in single `.db` file on Python 3.12 (`pysqlite3` + `sqlite-vec`)
- [x] Measure size for 10k × 384-dim vectors (float32 vec0: 15.26 MB; int8 blob: 3.92 MB)
- [x] Document Android JNI feasibility — see `logs/mobile-sqlite-vec-spike.json`

### N-08-05 Mobile index builder

- [x] Input: tier parquet + `food_aliases.parquet`
- [x] Output: `indexes/nutri-mobile/vectors.db`
- [x] Columns: id, source, name, name_normalized, kcal, protein, carb, fat, fiber, search_text
- [x] Reuse `hybrid_search` scoring logic (alias + keyword + vector)

### N-08-06 int8 quantization

- [x] Embed with 384-dim model (float32 at build time)
- [x] Store int8 vectors + scale per row (`embedding_int8`, `quant_scale`)
- [x] Validate recall@5 overlap 100% on probe queries (float32 vec0 search)

### N-08-07 Compact lexicon

- [x] SQLite FTS5 on `search_text` + alias table
- [x] Target ≤8 MB — actual ~1.6 MB

---

## Block C — Tiny embedder

### N-08-09 Export embedder ONNX

- [x] Export `BAAI/bge-small-en-v1.5` to ONNX
- [x] Dynamic quant int8 — **33.8 MB** on disk (≤35 MB)
- [x] Runtime: `onnxruntime` CPU (Python reference)
- [x] Same normalize/tokenize contract as desktop embedder

---

## Block D — Intent expansion

### N-08-11 NL → structured items

- [x] Pattern: `Quantas calorias tem {portion} de {food}?` → lookup item
- [x] Pattern: `calorias {food} {portion}` variants
- [x] Pattern: `quanto de {macro} tem {food}` → lookup + highlight field
- [x] Golden file: `tests/fixtures/mobile_nl_intents.jsonl` (53 utterances)

### N-08-12 Compare intent

- [x] Pattern: `{foodA} ou {foodB}` / `mais proteína` / `qual tem mais`
- [x] Output: `CompareIntent(food_a, food_b, field=protein|kcal|...)`

### N-08-13 Substitute intent

- [x] Pattern: `opção mais leve` / `substituto` / `menos carboidrato`
- [x] Output: `SubstituteIntent(food, optimize=carb|kcal|fat)`

---

## Block E — Rule engine

### N-08-14 Reasoning engine

- [x] `CompareEngine`: retrieve both foods, compare numeric field, template answer
- [x] `SubstituteEngine`: search same category, filter lower macro, rank
- [x] Reuse `scale_nutrient()` — **BR-RET-002**
- [x] Source boost — **BR-RET-001**
- [x] No LLM calls

### N-08-15 NL templates

- [x] PT-BR templates for compare, substitute, single lookup prose
- [x] Cite sources (TACO / OFF) in every template
- [x] Match desktop tone where possible (short, factual)

### N-08-16 Mobile orchestrator

- [x] `MobileNutriAssistant.ask()` — route intent → lookup | compare | substitute
- [x] Shared interface with `NutriAssistant` for parity tests
- [x] Mode flag: `--runtime mobile` in CLI

---

## Block F — Pack builder

### N-08-17 Build pack

- [x] `python scripts/mobile/build_pack.py`
- [x] Bundle: `vectors.db` + `lexicon.db` + `embedder.onnx` + `manifest.json`
- [x] xz compress single `nutri-mobile.pack`
- [x] Output: `indexes/nutri-mobile/nutri-mobile.pack` (**36.7 MB**)

### N-08-18 Size gate

- [x] `scripts/validate-nutri-mobile-pack.sh`
- [x] Assert total ≤200 MB
- [x] Assert manifest checksums match
- [x] Run golden + parity tests

---

## Block G — Parity validation

### N-08-19 Parity benchmark

- [x] Compare mobile vs desktop **lookup path** on G1–G5 (must match)
- [x] 20 NL queries: numeric accuracy **95%** vs desktop lookup
- [x] Latency p95 **10.9 ms** on reference CPU (≪500 ms target)
- [x] Log: `logs/mobile-parity-benchmark.json`

### N-08-21 … N-08-23 Tests

- [x] `test_mobile_intent.py` — NL patterns
- [x] `test_mobile_reasoning.py` — compare/substitute math
- [x] `test_mobile_parity_golden.py` — G1–G5 on mobile pack

---

## Block H — Android spike

### N-08-20 Android integration

- [x] Update `docs/android-integration.md` with pack layout + load sequence
- [x] Document `:nutri-ml` module boundary
- [x] ONNX Runtime Mobile or sqlite-vec JNI evaluation notes
- [ ] Kotlin spike in `android-spike/` (optional — not started)

---

## Exit criteria (Phase 8 complete)

- [x] `nutri-mobile.pack` ≤200 MB (36.7 MB built)
- [x] G1–G5 pass on mobile runtime
- [x] NL parity ≥95% on 20-query set
- [x] Compare + substitute work without LLM
- [x] `validate-nutri-mobile-pack.sh` green
- [x] IMPLEMENTATION-PLAN lists Phase 8

---

## Command sketch

```bash
cd nutri-offline
source venv/bin/activate
export HF_HOME="$(pwd)/models/base"

python scripts/mobile/select_mobile_records.py
python scripts/mobile/build_mobile_index.py --device cuda
python scripts/mobile/build_mobile_lexicon.py
python scripts/mobile/export_embedder_onnx.py
python scripts/mobile/build_pack.py

./scripts/validate-nutri-mobile-pack.sh
python scripts/mobile/benchmark_mobile_parity.py
python scripts/app/nutri_cli.py ask "arroz 100g" --runtime mobile
```
