# Phase 10 tasks — Mobile QA benchmark (B20)

> **ID:** N-10 · Close GAP-PORT / GAP-POULTRY / GAP-SUBST  
> **Quality gate:** 100% on R10 + B20 · pack ≤200 MB · p95 ≤500 ms  
> **Status:** Phase 10 complete (Blocks A–E)  
> **Depends on:** [Phase 9](../09-semantic-engine/TASKS.md)

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [A — Household portions v2](#block-a--household-portions-v2-gap-port) | BR-PORT-002 implicit default units | ✅ |
| [B — Poultry disambiguation](#block-b--poultry-disambiguation-gap-poultry) | BR-NORM-004 peito default | ✅ |
| [C — Substitute semantics](#block-c--substitute-semantics-gap-subst) | BR-SUBST-001 staple filter | ✅ |
| [D — Measurement harness](#block-d--measurement-harness) | B20 fixture + scorecard script | ✅ |
| [E — Gate + promotion](#block-e--gate--promotion) | CI gate + docs cross-links | ✅ |

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
| QA-16 | Gate subcommand for B20 | `validate-nutri-mobile-pack.sh` | P1 | ✅ |
| QA-17 | Log snapshot after benchmark run | `logs/` | P1 | ✅ |
| QA-18 | Phase 10 README + TASKS | `phases/10-mobile-qa/` | P1 | ✅ |
| QA-19 | Benchmark doc | `docs/MOBILE-QA-BENCHMARK.md` | P1 | ✅ |
| QA-20 | Link from IMPLEMENTATION-PLAN | `IMPLEMENTATION-PLAN.md` | P1 | ✅ |

---

## Block A — Household portions v2 (GAP-PORT)

- [x] BR-PORT-002 implemented; golden + manual validation

---

## Block B — Poultry disambiguation (GAP-POULTRY)

- [x] BR-NORM-004 implemented; R05, B13, B19 pass

---

## Block C — Substitute semantics (GAP-SUBST)

- [x] BR-SUBST-001 implemented; R07, B17 pass

---

## Block D — Measurement harness

- [x] `mobile_qa_b20.jsonl` + `run_qa_benchmark.py`
- [x] Manual: R10 10/10 · B20 20/20

---

## Block E — Gate + promotion

- [x] `validate-nutri-mobile-pack.sh` runs B20 with `--fail-under 100 --log`
- [x] Gate unittest suite includes `test_substitute_*` + `test_mobile_qa_benchmark`
- [x] `docs/MOBILE-QA-BENCHMARK.md` promoted from local plan
- [x] `IMPLEMENTATION-PLAN.md` Phase 10 row
- [x] Manual: full gate green (`./scripts/validate-nutri-mobile-pack.sh`)

---

## Exit criteria (Phase 10 complete)

- [x] **R10:** 10/10 ✅
- [x] **B20:** 20/20 ✅
- [x] All new golden tests in CI gate
- [x] p95 latency ≤500 ms (Phase 9 benchmark in gate)
- [x] Pack ≤200 MB (gate size check)
- [x] B20 benchmark enforced in `validate-nutri-mobile-pack.sh`

---

## Progress

| Date | Commit | R10 ✅ | B20 ✅ | Notes |
|------|--------|--------|--------|-------|
| 2026-06-29 | baseline | 5/10 | — | Phase 9 smoke test |
| 2026-06-29 | Block A | — | — | BR-PORT-002 |
| 2026-06-29 | Blocks B–D | 10/10 | 20/20 | poultry + substitute + harness |
| 2026-06-29 | Block E | 10/10 | 20/20 | gate + phase close |
