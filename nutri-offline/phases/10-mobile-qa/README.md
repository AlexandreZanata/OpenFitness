# Phase 10 — Mobile QA benchmark (B20)

> **Status:** Complete · **R10 + B20: 100%** · **Parent:** [Phase 9](../09-semantic-engine/README.md)  
> **Goal:** Reach **100% pass** on regression **R10** and full benchmark **B20** for grounded, semantically correct, portion-realistic mobile answers.

---

## Why Phase 10

Phase 9 ships the five-layer semantic engine. Real-user smoke tests (2026-06-29) showed **50% pass on R10** — three quality gaps were closed in this phase:

| Gap | Symptom | Status |
|-----|---------|--------|
| GAP-PORT | `uma banana`, `um cacetinho` → 100g default | ✅ Block A |
| GAP-POULTRY | `frango grelhado` → coração | ✅ Block B |
| GAP-SUBST | `mais leve que arroz` → curau | ✅ Block C |

Full benchmark reference: [MOBILE-QA-BENCHMARK.md](../../docs/MOBILE-QA-BENCHMARK.md)

---

## Business rules

| ID | Rule |
|----|------|
| BR-PORT-002 | Article-only or bare-food phrases apply `default_unit` grams; explicit `Ng` never overridden |
| BR-NORM-004 | Qualified poultry phrases → peito default unless organ/cut named |
| BR-SUBST-001 | Staple substitutes stay in cereal/starch role; curau/desserts blocklisted |

---

## Exit criteria (complete)

- [x] R10 10/10 · B20 20/20
- [x] `run_qa_benchmark.py` + `mobile_qa_b20.jsonl`
- [x] `validate-nutri-mobile-pack.sh` enforces B20 at 100%
- [x] p95 ≤500 ms · pack ≤200 MB (inherited Phase 8–9 gate)

---

## Validation

```bash
# From repo root
./scripts/validate-nutri-mobile-pack.sh

# Or step-by-step inside nutri-offline/
cd nutri-offline && source venv/bin/activate
export HF_HOME="${PWD}/models/base"
export PYTHONPATH="scripts/mobile:scripts/app"

python scripts/mobile/build_synonyms.py   # after manual_synonyms.json edits
python scripts/mobile/run_qa_benchmark.py --set B20 --log
```

---

## Task index

See [TASKS.md](TASKS.md) for QA-01–QA-20 checklist.
