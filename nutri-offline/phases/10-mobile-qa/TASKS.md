# Phase 10 tasks — Mobile QA benchmark (B20)

> **ID:** N-10 · Close GAP-PORT / GAP-POULTRY / GAP-SUBST  
> **Quality gate:** 100% on R10 + B20 · pack ≤200 MB · p95 ≤500 ms  
> **Status:** Blocks A–D complete (R10 + B20 at 100%)  
> **Depends on:** [Phase 9](../09-semantic-engine/TASKS.md)

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [A — Household portions v2](#block-a--household-portions-v2-gap-port) | BR-PORT-002 implicit default units | ✅ |
| [B — Poultry disambiguation](#block-b--poultry-disambiguation-gap-poultry) | BR-NORM-004 peito default | ✅ |
| [C — Substitute semantics](#block-c--substitute-semantics-gap-subst) | BR-SUBST-001 staple filter | ✅ |
| [D — Measurement harness](#block-d--measurement-harness) | B20 fixture + scorecard script | ✅ |

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| QA-01 | Implicit count → default unit in `HouseholdPortionResolver` | `household_portions.py` | P0 | ✅ |
| QA-02 | Bread entries: `pao frances` / `cacetinho` unit `un` ~50g | `household_portions.json` | P0 | ✅ |
| QA-03 | Article-only NL path: `uma banana` → unit `media` | `household_portions.py`, `intent_parser.py` | P0 | ✅ |
| QA-04 | Golden fixture rows R02, R10, B14, B15, B20 | `household_portions.jsonl` | P0 | ✅ |
| QA-05 | Portion footer on all household hits | `response_formatter.py` | P1 | ✅ |
| QA-06 | Ontology phrases: `frango grelhado` | `food_ontology.json` | P0 | ✅ |
| QA-07 | Penalize organ cuts without organ token | `mobile_search.py` | P0 | ✅ |
| QA-08 | Manual synonym: `frango grelhado` → `taco:410` | `manual_synonyms.json` | P0 | ✅ |
| QA-09 | Golden: R05, B13, B19 | `semantic_v2_golden.jsonl` | P0 | ✅ |
| QA-10 | Category filter in `SubstituteEngine` | `reasoning_engine.py` | P0 | ✅ |
| QA-11 | Blocklist curau/doces for `arroz` | `substitute_rules.json` | P0 | ✅ |
| QA-12 | ±30% kcal band for “leve” scoring | `SubstituteEngine` | P1 | ✅ |
| QA-13 | Golden: R07, B17 | `substitute_golden.jsonl` | P0 | ✅ |
| QA-14 | Fixture `mobile_qa_b20.jsonl` | `tests/fixtures/` | P0 | ✅ |
| QA-15 | Script `run_qa_benchmark.py` | `scripts/mobile/` | P0 | ✅ |
| QA-16 | Gate subcommand for B20 | `validate-nutri-mobile-pack.sh` | P1 | ⬜ |
| QA-17 | Log snapshot after benchmark run | `logs/` | P1 | ✅ |

---

## Block A — Household portions v2 (GAP-PORT)

**Business rule BR-PORT-002:** When phrase is article-only (`um|uma|1 <food>`) or bare food with no explicit gram portion, apply the entry `default_unit` grams and cite source.

- [x] `default_unit` + `aliases` on `household_portions.json` entries
- [x] Golden + intent tests; manual CLI validation

**Exit:** R02, R10, B15, B20 portion semantics ✅

---

## Block B — Poultry disambiguation (GAP-POULTRY)

**Business rule BR-NORM-004:** Qualified poultry phrases resolve to peito default unless organ/cut named.

- [x] Ontology phrase `frango grelhado` on `meat.poultry.chicken`
- [x] Manual synonym `frango grelhado` → `taco:410` (rebuild `synonyms.db`)
- [x] `poultry_rerank_adjustment()` penalizes organ cuts (−0.30) and boosts peito (+0.10)
- [x] Golden: R05, B13, B19 in `semantic_v2_golden.jsonl`
- [x] Manual: `frango grelhado` → peito `taco:410` (~32g protein / 100g)

**Exit:** R05, B13, B19 ✅

---

## Block C — Substitute semantics (GAP-SUBST)

**Business rule BR-SUBST-001:** Staple substitute must be same meal role (cereal/starch).

- [x] `config/semantic/substitute_rules.json` + `substitute_rules.py`
- [x] `SubstituteEngine` staple pool + blocklist (no curau) + kcal band (QA-12)
- [x] Golden: `substitute_golden.jsonl` (R07, B17)
- [x] Manual: `mais leve que arroz` → cuscuz/arroz integral (not curau); `menos carboidrato` → batata

**Exit:** R07, B17 ✅

---

## Block D — Measurement harness

- [x] `tests/fixtures/mobile_qa_b20.jsonl` (20 rows)
- [x] `scripts/mobile/run_qa_benchmark.py --set R10|B20 [--log]`
- [x] Manual run: **R10 10/10 · B20 20/20** (2026-06-29)
- [ ] CI gate hook (QA-16 — optional follow-up)

**Exit:** Automatable 20/20 scorecard ✅

---

## Progress

| Date | Commit | R10 ✅ | B20 ✅ | Notes |
|------|--------|--------|--------|-------|
| 2026-06-29 | baseline | 5/10 | — | Phase 9 smoke test |
| 2026-06-29 | Block A | — | — | BR-PORT-002 |
| 2026-06-29 | Blocks B–D | 10/10 | 20/20 | poultry + substitute + harness |
