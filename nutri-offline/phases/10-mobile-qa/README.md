# Phase 10 — Mobile QA benchmark (B20)

> **Status:** In progress (Block A complete) · **Parent:** [Phase 9](../09-semantic-engine/README.md)  
> **Goal:** Reach **100% pass** on regression **R10** and full benchmark **B20** for grounded, semantically correct, portion-realistic mobile answers.

---

## Why Phase 10

Phase 9 ships the five-layer semantic engine. Real-user smoke tests (2026-06-29) showed **50% pass on R10** — three gaps remain:

| Gap | Symptom | Fix block |
|-----|---------|-----------|
| GAP-PORT | `uma banana`, `um cacetinho` → 100g default | Block A — household portions v2 |
| GAP-POULTRY | `frango grelhado` → coração | Block B — poultry disambiguation |
| GAP-SUBST | `mais leve que arroz` → curau | Block C — substitute semantics |

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

- [ ] **R10:** 10/10 ✅ (100% regression)
- [ ] **B20:** 20/20 ✅ (100% full benchmark)
- [ ] Measurement harness (`run_qa_benchmark.py`) in CI gate
- [ ] p95 latency still ≤500 ms; pack still ≤200 MB

---

## Quick validation

```bash
cd nutri-offline && source venv/bin/activate

# Household portions (Block A)
python scripts/mobile/household_portions.py "uma banana"
python -m unittest tests.test_household_portions -v

# Full benchmark (after harness — Block D)
python scripts/mobile/run_qa_benchmark.py --set B20
```
