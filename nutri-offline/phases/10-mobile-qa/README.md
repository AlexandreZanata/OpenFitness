# Phase 10 — Mobile QA benchmark (B20)

> **Status:** Blocks A–D complete · **R10 + B20: 100%** · **Parent:** [Phase 9](../09-semantic-engine/README.md)  
> **Goal:** Reach **100% pass** on regression **R10** and full benchmark **B20** for grounded, semantically correct, portion-realistic mobile answers.

---

## Why Phase 10

Phase 9 ships the five-layer semantic engine. Real-user smoke tests (2026-06-29) showed **50% pass on R10** — three gaps remain:

| Gap | Symptom | Fix block |
|-----|---------|-----------|
| GAP-PORT | `uma banana`, `um cacetinho` → 100g default | Block A — household portions v2 ✅ |
| GAP-POULTRY | `frango grelhado` → coração | Block B — poultry disambiguation ✅ |
| GAP-SUBST | `mais leve que arroz` → curau | Block C — substitute semantics ✅ |

Full plan: [MOBILE-QA-BENCHMARK.md](../../docs/MOBILE-QA-BENCHMARK.md)

---

## Business rules (Phase 10)

| ID | Rule |
|----|------|
| BR-PORT-002 | Article-only or bare-food phrases apply `default_unit` grams from `household_portions.json`; explicit `Ng` portions are never overridden |
| BR-NORM-004 | Qualified poultry phrases resolve to ontology default peito unless user names organ/cut |
| BR-SUBST-001 | Staple substitutes must stay in the same meal role (cereal/starch), not dessert/porridge |

---

## Exit criteria

- [x] **R10:** 10/10 ✅ (100% regression)
- [x] **B20:** 20/20 ✅ (100% full benchmark)
- [x] Measurement harness (`run_qa_benchmark.py`)
- [ ] CI gate integration (QA-16 — optional)
- [ ] p95 latency still ≤500 ms; pack still ≤200 MB (unchanged from Phase 9)

---

## Quick validation

```bash
cd nutri-offline && source venv/bin/activate
export HF_HOME="${PWD}/models/base"

# Rebuild synonyms after manual_synonyms.json changes
python scripts/mobile/build_synonyms.py

# Full benchmark
PYTHONPATH=scripts/mobile:scripts/app python scripts/mobile/run_qa_benchmark.py --set B20 --log

# Unit + integration golden tests
python -m unittest tests.test_substitute_golden tests.test_semantic_v2_golden -v
```
