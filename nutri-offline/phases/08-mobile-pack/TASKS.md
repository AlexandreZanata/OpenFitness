# Phase 8 tasks — Mobile pack (≤200 MB)

> **ID:** N-08 · Mobile capability parity  
> **Quality gate:** `nutri-mobile.pack` ≤200 MB; G1–G5 + NL parity set pass  
> **Status:** In progress (Block A complete; Block B started)  
> **Depends on:** [Phase 3](../03-vector-db-rag/TASKS.md) (data), [RAG V2 Phase B/C](../../docs/README-RAG-V2.md) (lookup path)

---

## Owner decisions (resolve before N-08-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Pack budget** | Hard 200 MB total | ✅ Locked |
| **On-device LLM** | None in v1 pack | ✅ Recommended — use rule engine |
| **Embedder** | bge-small-en-v1.5 int8 ONNX · multilingual-e5-small | ⬜ A/B in N-08-10 |
| **Index runtime** | sqlite-vec (recommended) · bundled LanceDB lite | ⬜ Spike N-08-04 |
| **OFF tier C size** | 5k · 8k · 10k products | ⬜ Tune in N-08-05 |
| **Android v1** | Python parity runtime first · JNI spike parallel | ⬜ N-08-20 |

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [A — Specification](#block-a--specification) | Capability matrix + budget | ✅ |
| [B — Mobile index](#block-b--mobile-index) | sqlite-vec int8 build | 🔄 |
| [C — Tiny embedder](#block-c--tiny-embedder) | ONNX export ≤35 MB | ⬜ |
| [D — Intent expansion](#block-d--intent-expansion) | NL → lookup/compare/substitute | ⬜ |
| [E — Rule engine](#block-e--rule-engine) | Replace LLM reasoning | ⬜ |
| [F — Pack builder](#block-f--pack-builder) | Single artifact + size gate | ⬜ |
| [G — Parity validation](#block-g--parity-validation) | vs desktop golden set | ⬜ |
| [H — Android spike](#block-h--android-spike) | OpenFitness integration path | ⬜ |

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-08-01 | Capability matrix doc | `docs/MOBILE-CAPABILITY-MATRIX.md` | P0 | ✅ |
| N-08-02 | Budget spec + manifest schema | `scripts/mobile/pack_schema.json`, `pack_budget.py` | P0 | ✅ |
| N-08-03 | Record tier selector (A/B/C) | `scripts/mobile/select_mobile_records.py` | P0 | ✅ |
| N-08-04 | sqlite-vec index spike | `scripts/mobile/spike_sqlite_vec.py` | P0 | ✅ |
| N-08-05 | Mobile index builder | `scripts/mobile/build_mobile_index.py` | P0 | ⬜ |
| N-08-06 | int8 vector quantization | inside `build_mobile_index.py` | P0 | ⬜ |
| N-08-07 | Compact FTS + alias sqlite | `scripts/mobile/build_mobile_lexicon.py` | P0 | ⬜ |
| N-08-08 | Mobile hybrid search port | `scripts/mobile/mobile_search.py` | P0 | ⬜ |
| N-08-09 | Export embedder ONNX | `scripts/mobile/export_embedder_onnx.py` | P0 | ⬜ |
| N-08-10 | Embedder A/B on mobile golden | extend `embedder_benchmark.py` | P1 | ⬜ |
| N-08-11 | Intent parser NL expansion | extend `intent_parser.py` | P0 | ⬜ |
| N-08-12 | Compare intent + patterns | `scripts/mobile/intents_compare.py` | P0 | ⬜ |
| N-08-13 | Substitute intent + patterns | `scripts/mobile/intents_substitute.py` | P0 | ⬜ |
| N-08-14 | Reasoning engine | `scripts/mobile/reasoning_engine.py` | P0 | ⬜ |
| N-08-15 | NL response templates | `scripts/mobile/response_templates.py` | P0 | ⬜ |
| N-08-16 | Mobile orchestrator | `scripts/mobile/mobile_assistant.py` | P0 | ⬜ |
| N-08-17 | Pack builder | `scripts/mobile/build_pack.py` | P0 | ⬜ |
| N-08-18 | Size gate script | `scripts/validate-nutri-mobile-pack.sh` | P0 | ⬜ |
| N-08-19 | Parity benchmark | `scripts/mobile/benchmark_mobile_parity.py` | P0 | ⬜ |
| N-08-20 | Android integration update | `docs/android-integration.md` | P1 | ⬜ |
| N-08-21 | Unit tests — intent NL | `tests/test_mobile_intent.py` | P0 | ⬜ |
| N-08-22 | Unit tests — reasoning | `tests/test_mobile_reasoning.py` | P0 | ⬜ |
| N-08-23 | Golden parity tests | `tests/test_mobile_parity_golden.py` | P0 | ⬜ |
| N-08-24 | CLI mobile mode | `nutri_cli.py ask --runtime mobile` | P1 | ⬜ |
| N-08-25 | Phase cross-links | IMPLEMENTATION-PLAN, RAG V2, Phases 3/6/7 | P1 | ⬜ |

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
- [x] Document Android JNI feasibility (read-only sqlite) — see `logs/mobile-sqlite-vec-spike.json`

### N-08-05 Mobile index builder

- [ ] Input: tier parquet + `food_aliases.parquet`
- [ ] Output: `indexes/nutri-mobile/vectors.db`
- [ ] Columns: id, source, name, name_normalized, kcal, protein, carb, fat, fiber, search_text
- [ ] Reuse `hybrid_search` scoring logic (alias + keyword + vector)

### N-08-06 int8 quantization

- [ ] Embed with 384-dim model (float32 at build time)
- [ ] Store int8 vectors + scale per row or global scale
- [ ] Validate recall@5 vs float index on 50 probe queries — target ≥95% overlap with desktop top-5

### N-08-07 Compact lexicon

- [ ] SQLite FTS5 on `search_text` + alias table
- [ ] Target ≤8 MB for aliases + FTS

---

## Block C — Tiny embedder

### N-08-09 Export embedder ONNX

- [ ] Export `BAAI/bge-small-en-v1.5` (or e5-small) to ONNX
- [ ] Dynamic quant int8 — target **≤35 MB** on disk
- [ ] Runtime: `onnxruntime` CPU (Python reference; TFLite optional in Block H)
- [ ] Same normalize/tokenize contract as desktop embedder

### N-08-10 Embedder A/B (mobile golden)

- [ ] Run 50 mobile-tier queries against float vs int8 ONNX
- [ ] Log to `logs/mobile-embedder-ab.json`
- [ ] Pick model that meets recall target within size budget

---

## Block D — Intent expansion

### N-08-11 NL → structured items

Extend `intent_parser.py`:

- [ ] Pattern: `Quantas calorias tem {portion} de {food}?` → lookup item
- [ ] Pattern: `calorias {food} {portion}` variants
- [ ] Pattern: `quanto de {macro} tem {food}` → lookup + highlight field
- [ ] Golden file: `tests/fixtures/mobile_nl_intents.jsonl` (50+ utterances)

### N-08-12 Compare intent

- [ ] Pattern: `{foodA} ou {foodB}` / `mais proteína` / `qual tem mais`
- [ ] Output: `CompareIntent(food_a, food_b, field=protein|kcal|...)`

### N-08-13 Substitute intent

- [ ] Pattern: `opção mais leve` / `substituto` / `menos carboidrato`
- [ ] Output: `SubstituteIntent(food, optimize=carb|kcal|fat)`

---

## Block E — Rule engine

### N-08-14 Reasoning engine

- [ ] `CompareEngine`: retrieve both foods, compare numeric field, template answer
- [ ] `SubstituteEngine`: search same category, filter lower macro, rank
- [ ] Reuse `scale_nutrient()` — **BR-RET-002**
- [ ] Source boost — **BR-RET-001**
- [ ] No LLM calls

### N-08-15 NL templates

- [ ] PT-BR templates for compare, substitute, single lookup prose
- [ ] Cite sources (TACO / OFF) in every template
- [ ] Match desktop tone where possible (short, factual)

### N-08-16 Mobile orchestrator

- [ ] `MobileNutriAssistant.ask()` — route intent → lookup | compare | substitute
- [ ] Shared interface with `NutriAssistant` for parity tests
- [ ] Mode flag: `--runtime mobile` in CLI

---

## Block F — Pack builder

### N-08-17 Build pack

- [ ] `python scripts/mobile/build_pack.py`
- [ ] Bundle: `vectors.db` + `lexicon.db` + `embedder.onnx` + `manifest.json`
- [ ] Optional: zstd compress single `nutri-mobile.pack`
- [ ] Output: `indexes/nutri-mobile/nutri-mobile.pack`

### N-08-18 Size gate

- [ ] `scripts/validate-nutri-mobile-pack.sh`
- [ ] Assert total ≤200 MB (200 * 1024 * 1024 bytes)
- [ ] Assert manifest checksums match
- [ ] Run golden + parity tests

---

## Block G — Parity validation

### N-08-19 Parity benchmark

- [ ] Compare mobile vs desktop **lookup path** on G1–G5 (must match)
- [ ] 20 NL queries: numeric accuracy ≥95% vs desktop lookup (not LLM)
- [ ] Latency p95 ≤500 ms on documented reference CPU
- [ ] Log: `logs/mobile-parity-benchmark.json`

### N-08-21 … N-08-23 Tests

- [ ] `test_mobile_intent.py` — NL patterns
- [ ] `test_mobile_reasoning.py` — compare/substitute math
- [ ] `test_mobile_parity_golden.py` — G1–G5 on mobile pack

---

## Block H — Android spike

### N-08-20 Android integration

- [ ] Update `docs/android-integration.md` with pack layout + load sequence
- [ ] Document `:nutri-ml` module boundary
- [ ] ONNX Runtime Mobile or sqlite-vec JNI evaluation
- [ ] No Kotlin in Phase 8 unless spike folder created (`android-spike/`)

---

## Adaptations to upstream phases

| Phase | Task addition | Notes |
|-------|---------------|-------|
| **N-03** | N-03-09 mobile index contract | Link from Phase 3 TASKS |
| **N-06** | Desktop-only label | GGUF not in mobile pack |
| **N-07** | N-07-10 mobile runtime adapter | Shared ports, dual runtime |
| **RAG V2** | Phase D block | This phase |

---

## Exit criteria (Phase 8 complete)

- [ ] `nutri-mobile.pack` ≤200 MB
- [ ] G1–G5 pass on mobile runtime
- [ ] NL parity ≥95% on 20-query set
- [ ] Compare + substitute work without LLM
- [ ] `validate-nutri-mobile-pack.sh` green in CI
- [ ] IMPLEMENTATION-PLAN lists Phase 8

---

## Command sketch (when implemented)

```bash
cd nutri-offline
source venv/bin/activate
export HF_HOME="$(pwd)/models/base"

# Build mobile pack
python scripts/mobile/select_mobile_records.py
python scripts/mobile/build_mobile_index.py --device cuda
python scripts/mobile/export_embedder_onnx.py
python scripts/mobile/build_pack.py

# Validate
./scripts/validate-nutri-mobile-pack.sh

# Parity vs desktop
python scripts/mobile/benchmark_mobile_parity.py
python scripts/app/nutri_cli.py ask "arroz 100g" --runtime mobile
```
