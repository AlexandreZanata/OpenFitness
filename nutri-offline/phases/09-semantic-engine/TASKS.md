# Phase 9 tasks — Semantic nutrition engine (v2)

> **ID:** N-09 · Normalization-first mobile retrieval  
> **Quality gate:** typo/ontology/portion golden set + pack ≤200 MB  
> **Status:** Block C complete (N-09-03 done)  
> **Depends on:** [Phase 8](../08-mobile-pack/TASKS.md)

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [A — Spell-fix](#block-a--spell-fix) | Layer 1 orthographic correction | ✅ |
| [B — Synonyms](#block-b--synonyms) | Layer 2 alias graph v2 | ✅ |
| [C — Ontology](#block-c--ontology) | Layer 3 food hierarchy | ✅ |
| [D — Multi-surface index](#block-d--multi-surface-index) | Layer 4 semantic surfaces | ⬜ |
| [E — Household portions](#block-e--household-portions) | Layer 5 portion rules | ⬜ |
| [F — Resolver pipeline](#block-f--resolver-pipeline) | SemanticResolver entry point | ⬜ |
| [G — Pack v2 + gate](#block-g--pack-v2--gate) | schema_version 2 rebuild | ⬜ |

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-09-01 | Spell-fix lexicon | `scripts/mobile/spell_normalize.py` | P0 | ✅ |
| N-09-02 | Synonym graph v2 | Expand `food_aliases` + `synonyms.db` | P0 | ✅ |
| N-09-03 | Ontology | `config/semantic/food_ontology.json` + resolver | P0 | ✅ |
| N-09-04 | Multi-surface builder | `build_semantic_surfaces.py` → ~24k rows | P0 | ⬜ |
| N-09-05 | Household portions | `data/semantic/household_portions.json` + rules | P0 | ⬜ |
| N-09-06 | Resolver pipeline | `SemanticResolver` replaces direct `mobile_search` entry | P0 | ⬜ |
| N-09-07 | Pack v2 + gate | Rebuild pack; golden typo/portion cases | P0 | ⬜ |
| N-09-08 | Optional intent embedder | 50 prototype vectors if regex < 90% | P1 | ⬜ |
| N-09-09 | Unit tests — spell-fix | `tests/test_spell_normalize.py` | P0 | ✅ |
| N-09-10 | Phase docs + cross-links | IMPLEMENTATION-PLAN, SEMANTIC-ENGINE-V2 | P1 | ✅ |
| N-09-11 | Unit tests — synonyms | `tests/test_synonym_resolver.py` | P0 | ✅ |
| N-09-12 | Unit tests — ontology | `tests/test_ontology_resolver.py` | P0 | ✅ |

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

- [ ] Per-record K semantic surfaces (alias, category, prep, FAQ-style)
- [ ] int8 vectors within 90 MB budget
- [ ] Intent prototype table (regex first; embed later if needed)

---

## Block E — Household portions

### N-09-05 Household portions

- [ ] `data/semantic/household_portions.json` (~200–500 rows)
- [ ] Extend `PORTION_PATTERN` / NL patterns — never invent grams (BR-PORT-001)
- [ ] Golden: `uma manga inteira` → 230g scaled macros

---

## Block F — Resolver pipeline

### N-09-06 SemanticResolver

- [ ] Orchestrate layers 1–5 before vector search
- [ ] Replace direct `mobile_search` entry in `MobileNutriAssistant`
- [ ] Debug metadata: corrections, ontology path, portion source

---

## Block G — Pack v2 + gate

### N-09-07 Pack v2

- [ ] Bump `pack.manifest.json` `schema_version` to 2
- [ ] Extend `validate-nutri-mobile-pack.sh` with typo/portion golden cases
- [ ] Rebuild pack; assert ≤200 MB

---

## Exit criteria (Phase 9 complete)

- [ ] All Block A–G tasks done
- [ ] Five v2 golden flows pass (see README)
- [ ] p95 latency ≤500 ms
- [ ] Pack ≤200 MB
