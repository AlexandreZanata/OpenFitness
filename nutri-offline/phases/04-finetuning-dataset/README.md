# Phase 4 — Fine-tuning dataset generation

> **Status:** Done (2026-06-28)  
> **Parent:** [Phase 2](../02-data-normalization/README.md)  
> **Goal:** Generate 2,000–5,000 high-quality ChatML Q&A pairs for supervised fine-tuning.

---

## Objective

Fine-tuning teaches the model **how to reason and respond** about nutrition — not to memorize tables. Generate diverse question→answer pairs from normalized data using templates, paraphrasing, and reasoning scenarios.

---

## Output format (ChatML JSONL)

```json
{"messages": [
  {"role": "system", "content": "Você é um assistente especialista em nutrição..."},
  {"role": "user", "content": "Quantas calorias tem 150g de Arroz, tipo 1, cozido segundo a TACO?"},
  {"role": "assistant", "content": "Segundo a TACO (NEPA/UNICAMP), 150g de Arroz, tipo 1, cozido fornecem aproximadamente 192 kcal, 3.8g de proteína..."}
]}
```

File layout:

```
data/datasets/
├── train.jsonl          # 90% (2,702 examples)
├── val.jsonl            # 10% (298 examples)
├── raw_generated.jsonl  # full set with generation_log
├── generation_log.jsonl
├── stats.json
└── manual_review/sample_200.jsonl
```

---

## Generation strategies

| Strategy | Target % | Generated |
|----------|----------|-----------|
| **Direct lookup** | 40% | 1,200 |
| **Comparison** | 15% | 450 |
| **Portion math** | 15% | 450 |
| **Substitution** | 10% | 300 |
| **Allergen / ingredients** | 10% | 300 |
| **Reasoning / IG** | 10% | 300 |

---

## Quality rules

| Rule | Description | Status |
|------|-------------|--------|
| BR-DS-001 | Every numeric answer traces to source in `generation_log` | ✅ |
| BR-DS-002 | No answer invents nutrients not in source data | ✅ |
| BR-DS-003 | Portuguese (BR) primary — 90%+ examples | ✅ 96.9% |
| BR-DS-004 | System prompt consistent across all examples | ✅ |
| BR-DS-005 | Manual review of 10% sample before training | ✅ |

---

## Commands

```bash
cd nutri-offline
source venv/bin/activate

# Generate full dataset (~2s on existing foods.parquet)
python scripts/dataset/run_all.py --target 3000

# Repo gate (from project root)
./scripts/validate-nutri-dataset.sh
```

---

## Out of scope

| Item | Reason |
|------|--------|
| DPO preference pairs | Phase 5 follow-up if quality insufficient |
| Synthetic answers without source grounding | Violates BR-DS-001 |
| English-only dataset | App target is PT-BR |
| LLM paraphrase pass | Deferred — template variants sufficient for v1 |

---

## Definition of done

- [x] ≥ 2,000 train examples + ≥ 200 val examples
- [x] All examples pass automated grounding check (numbers match source)
- [x] 10% manual review completed — quality notes documented
- [x] Train/val split stratified by template type
- [x] Ready for [Phase 5](../05-finetuning-training/TASKS.md)

---

**References:** [TASKS.md](TASKS.md) · [ChatML format](https://github.com/openai/openai-python/blob/main/chatml.md)
