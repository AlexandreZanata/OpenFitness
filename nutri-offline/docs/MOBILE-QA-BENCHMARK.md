# Mobile QA benchmark (B20)

> **Phase:** [10 — Mobile QA](../phases/10-mobile-qa/README.md) · **Status:** R10 + B20 **100%** (2026-06-29)  
> **Baseline (2026-06-29):** R10 **50%** (5/10 ✅) · **Target:** R10 + B20 **100%**

---

## Goal

Every mobile answer must be **grounded, semantically correct, and portion-realistic** — not merely “in the database”.

| Gap | Symptom | Business rule |
|-----|---------|---------------|
| GAP-PORT | `uma banana`, `um cacetinho` → 100g | BR-PORT-002 |
| GAP-POULTRY | `frango grelhado` → coração | BR-NORM-004 |
| GAP-SUBST | `mais leve que arroz` → curau | BR-SUBST-001 |

---

## Scoring rubric

| Score | Criteria |
|-------|----------|
| ✅ Good | Correct mode; expected `record_id`; macros ±2%; portion grams match; source cited |
| ⚠️ Partial | Right family, wrong cut/portion/substitute; or missing portion footer |
| ❌ Wrong | Wrong food/mode, fabricated macros, or no grounded source |

---

## Regression R10 (exact wording — do not edit)

| ID | Question | Baseline | Expected after fix |
|----|----------|----------|-------------------|
| R01 | `100g de arror` | ✅ | unchanged |
| R02 | `Quantas calorias tem um cacetinho?` | ⚠️ 100g | ✅ ~50g pão francês |
| R03 | `100g de carne vermelha` | ✅ | unchanged |
| R04 | `Quantas calorias tem uma manga inteira?` | ✅ | unchanged |
| R05 | `Quanto de proteína tem 100g de frango grelhado?` | ❌ coração | ✅ peito ~32g |
| R06 | `Qual tem mais proteína: frango ou ovo?` | ✅ | unchanged |
| R07 | `Existe opção mais leve que arroz?` | ⚠️ curau | ✅ staple substitute |
| R08 | `Quantas calorias tem 170g de iogurte vigor?` | ✅ | unchanged |
| R09 | `arroz 100g, feijão 100g` | ✅ | unchanged |
| R10 | `Quantas calorias tem uma banana?` | ⚠️ 100g | ✅ ~86g banana |

---

## Benchmark B20 (= R10 + 10 new)

See [Phase 10 TASKS](../phases/10-mobile-qa/TASKS.md) for full B11–B20 table.

---

## Measurement workflow

```bash
cd nutri-offline && source venv/bin/activate

# After config/semantic changes — rebuild pack
python scripts/mobile/build_mobile_index.py --device cuda
python scripts/mobile/build_mobile_lexicon.py
python scripts/mobile/build_pack.py

# Household portion smoke (Block A)
python scripts/mobile/household_portions.py "uma banana"
python -m unittest tests.test_household_portions -v

# Full benchmark (R10 + B20)
PYTHONPATH=scripts/mobile:scripts/app python scripts/mobile/run_qa_benchmark.py --set B20 --log
```

---

## TACO anchor reference

| record_id | Name | Use when |
|-----------|------|----------|
| `taco:3` | Arroz cozido | arroz / typo arror |
| `taco:53` | Pão francês | cacetinho / pão de sal |
| `taco:182` | Banana prata | banana / uma banana |
| `taco:228` | Manga Haden | manga inteira |
| `taco:377` | Patinho grelhado | carne vermelha |
| `taco:410` | Peito frango grelhado | frango grelhado |
| `taco:488` | Ovo cozido | ovo |
| `taco:561` | Feijão carioca | feijão generic |

---

## References

- [SEMANTIC-ENGINE-V2.md](SEMANTIC-ENGINE-V2.md) — Layer 5 portions (BR-PORT-001/002)
- [Phase 9 TASKS](../phases/09-semantic-engine/TASKS.md)
