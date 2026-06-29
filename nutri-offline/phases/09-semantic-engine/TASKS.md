# Phase 9 tasks — Semantic nutrition engine (v2)

> **ID:** N-09 · Normalization-first mobile retrieval  
> **Quality gate:** typo/ontology/portion golden set + pack ≤200 MB  
> **Status:** Phase 9 complete (N-09-01–08, N-09-17 done)  
> **Depends on:** [Phase 8](../08-mobile-pack/TASKS.md)

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [A — Spell-fix](#block-a--spell-fix) | Layer 1 orthographic correction | ✅ |
| [B — Synonyms](#block-b--synonyms) | Layer 2 alias graph v2 | ✅ |
| [C — Ontology](#block-c--ontology) | Layer 3 food hierarchy | ✅ |
| [D — Multi-surface index](#block-d--multi-surface-index) | Layer 4 semantic surfaces | ✅ |
| [E — Household portions](#block-e--household-portions) | Layer 5 portion rules | ✅ |
| [F — Resolver pipeline](#block-f--resolver-pipeline) | SemanticResolver entry point | ✅ |
| [G — Pack v2 + gate](#block-g--pack-v2--gate) | schema_version 2 rebuild | ✅ |
| [H — Latency + intent gate](#block-h--latency--intent-gate) | p95 ≤500 ms; regex ≥90% | ✅ |

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-09-01 | Spell-fix lexicon | `scripts/mobile/spell_normalize.py` | P0 | ✅ |
| N-09-02 | Synonym graph v2 | Expand `food_aliases` + `synonyms.db` | P0 | ✅ |
| N-09-03 | Ontology | `config/semantic/food_ontology.json` + resolver | P0 | ✅ |
| N-09-04 | Multi-surface builder | `build_semantic_surfaces.py` → ~24k rows | P0 | ✅ |
| N-09-05 | Household portions | `config/semantic/household_portions.json` + rules | P0 | ✅ |
| N-09-06 | Resolver pipeline | `SemanticResolver` replaces direct `mobile_search` entry | P0 | ✅ |
| N-09-07 | Pack v2 + gate | Rebuild pack; golden typo/portion cases | P0 | ✅ |
| N-09-08 | Optional intent embedder | 50 prototype vectors if regex < 90% | P1 | ✅ skip |
| N-09-17 | Latency + intent gate | `benchmark_semantic_v2.py` + `intent_regex_gate.py` | P0 | ✅ |
| N-09-09 | Unit tests — spell-fix | `tests/test_spell_normalize.py` | P0 | ✅ |
| N-09-10 | Phase docs + cross-links | IMPLEMENTATION-PLAN, SEMANTIC-ENGINE-V2 | P1 | ✅ |
| N-09-11 | Unit tests — synonyms | `tests/test_synonym_resolver.py` | P0 | ✅ |
| N-09-12 | Unit tests — ontology | `tests/test_ontology_resolver.py` | P0 | ✅ |
| N-09-13 | Unit tests — household portions | `tests/test_household_portions.py` | P0 | ✅ |
| N-09-14 | Unit tests — semantic resolver | `tests/test_semantic_resolver.py` | P0 | ✅ |
| N-09-15 | Unit tests — semantic surfaces | `tests/test_semantic_surfaces.py` | P0 | ✅ |
| N-09-16 | Unit tests — v2 golden gate | `tests/test_semantic_v2_golden.py` | P0 | ✅ |
| N-09-18 | Unit tests — intent regex gate | `tests/test_intent_regex_gate.py` | P0 | ✅ |
| N-09-19 | Unit tests — v2 latency | `tests/test_semantic_v2_latency.py` | P0 | ✅ |

---

## Block A — Spell-fix

### N-09-01 Spell-fix lexicon

- [x] Implement `spell_normalize.py` with Levenshtein correction (BR-NORM-001)
- [x] Build lexicon from mobile `lexicon.db` (aliases + FTS tokens)
- [x] Tie-break: longest common prefix + alias frequency
- [x] Strip leading PT-BR prepositions (`de`, `da`, `do`, …)
- [x] Wire into `MobileSearcher.search()` before alias/vector lookup
- [x] Golden fixture: `tests/fixtures/spell_corrections.jsonl`
- [x] Manual validation: `100g de arror` → TACO arroz

---

## Block B — Synonyms

### N-09-02 Synonym graph v2

- [x] Manual BR seeds in `config/semantic/manual_synonyms.json`
- [x] Build `synonyms.db` from manual seeds + mobile-scoped `food_aliases.parquet`
- [x] `SynonymResolver` — colloquial phrase → record_id(s) with default policy (BR-NORM-002)
- [x] Wire into `MobileSearcher.search()` before alias/vector lookup
- [x] Bundle `synonyms.db` in mobile pack via `build_pack.py`
- [x] Golden fixture: `tests/fixtures/synonym_resolutions.jsonl`
- [x] Manual validation: `cacetinho`, `carne vermelha`, `pao de sal` → TACO rows

---

## Block C — Ontology

### N-09-03 Ontology

- [x] `config/semantic/food_ontology.json` hierarchy (bovine, poultry, bread)
- [x] `OntologyResolver` — category phrases → candidate record IDs
- [x] Default policy (patinho for bovine) + clarify note in lookup footer (BR-NORM-003)
- [x] Wired into `MobileSearcher.search()` when synonym layer misses
- [x] Golden fixture: `tests/fixtures/ontology_resolutions.jsonl`
- [x] Manual validation: `100g carne bovina` → patinho TACO with clarify note

---

## Block D — Multi-surface index

### N-09-04 Multi-surface builder

- [x] `semantic_surfaces.py` — per-record surfaces (canonical, alias, category, prep, FAQ) with tier caps (BR-SURF-001)
- [x] `build_semantic_surfaces.py` — export parquet + stats (~28k surfaces, int8 ≤90 MB)
- [x] `config/semantic/intent_prototypes.json` + `intent_prototypes` table in lexicon (regex-first)
- [x] `build_mobile_index.py --multi-surface` → `food_surfaces` + `food_surface_vec`
- [x] `MobileSearcher` prefers surface vector index when present
- [x] Golden fixture: `tests/fixtures/semantic_surfaces.jsonl`
- [x] Manual validation: `build_semantic_surfaces.py --record-id taco:3` + CLI lookup

---

## Block E — Household portions

### N-09-05 Household portions

- [x] `config/semantic/household_portions.json` (mango, banana, apple, egg seeds)
- [x] `HouseholdPortionResolver` — unit phrase → grams with source (BR-PORT-001)
- [x] Extend `intent_parser.py` NL + shorthand paths via `_apply_household_portions`
- [x] Portion source cited in lookup footer via `response_formatter.py`
- [x] Golden fixture: `tests/fixtures/household_portions.jsonl`
- [x] Manual validation: `Quantas calorias tem uma manga inteira?` → 230g / ~146 kcal TACO

---

## Block F — Resolver pipeline

### N-09-06 SemanticResolver

- [x] `semantic_resolver.py` orchestrates layers 1–3 (spell → synonym → ontology)
- [x] Wired into `MobileSearcher.normalize_food_query()` and `search()`; exposes `last_resolution`
- [x] `MobileNutriAssistant` debug payload: `semantic` + `portions` when `--debug`
- [x] Golden fixture: `tests/fixtures/semantic_resolutions.jsonl`
- [x] Manual validation: `semantic_resolver.py --json` and `nutri_cli.py ask … --debug --json`

---

## Block G — Pack v2 + gate

### N-09-07 Pack v2

- [x] Bump `pack.manifest.json` `schema_version` to 2 with `surface_count` + `semantic_engine: v2`
- [x] Extend `validate-nutri-mobile-pack.sh` with schema v2 check + `test_semantic_v2_golden`
- [x] Rebuild pack (70.9 MB compressed); assert ≤200 MB
- [x] Golden fixture: `tests/fixtures/semantic_v2_golden.jsonl` (arror, carne vermelha, cacetinho, manga, ontology)

---

## Block H — Latency + intent gate

### N-09-08 Optional intent embedder (skipped)

- [x] Measure regex accuracy on `mobile_nl_intents.jsonl` via `intent_regex_gate.py` (BR-INT-001)
- [x] Result: **100%** accuracy (53/53) ≥ 90% threshold — **embedder not required**
- [x] Regex-first `intent_prototypes.json` retained in lexicon for future optional embed path

### N-09-17 Latency gate

- [x] `benchmark_semantic_v2.py` — p95 lookup latency on v2 golden + baseline queries
- [x] Target ≤500 ms (measured **~82 ms** p95 on dev CPU after warmup)
- [x] Golden tests: `tests/test_semantic_v2_latency.py`
- [x] Wired into `validate-nutri-mobile-pack.sh`

---

## Exit criteria (Phase 9 complete)

- [x] All Block A–H tasks done
- [x] Five v2 golden flows pass (see README)
- [x] p95 latency ≤500 ms
- [x] Pack ≤200 MB (`schema_version` 2)
