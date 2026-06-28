# Phase 4 tasks — Fine-tuning dataset

> **ID:** N-04 · ChatML Q&A generation  
> **Quality gate:** ≥ 2k examples; 100% grounding check pass; 10% manual review  
> **Status:** Done (2026-06-28)  
> **Depends on:** [Phase 2](../02-data-normalization/TASKS.md)

---

## Owner decisions (resolve before N-04-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Target size** | 2,000 (min) · 3,000 · 5,000 (recommended upper) | ✅ 3,000 |
| **Language mix** | 95% PT-BR · 80/20 PT/EN | ✅ 96.9% PT-BR |
| **Paraphrasing** | Template only · LLM paraphrase (recommended) | ✅ Template variants (5+ per category) |
| **System prompt language** | PT-BR (recommended) · EN | ✅ PT-BR |
| **TACO weight** | Oversample TACO (recommended for BR focus) | ✅ TACO pool ×8 oversample |

---

## 0. Prerequisites

- [x] Phase 2 complete — `foods.parquet`
- [x] Read [README.md](README.md) generation strategies
- [x] Define system prompt text (single canonical version)

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-04-01 | Question templates | `scripts/dataset/templates.py` | P0 | ✅ |
| N-04-02 | Answer generator | `scripts/dataset/answers.py` | P0 | ✅ |
| N-04-03 | Main generation pipeline | `scripts/dataset/generate.py` | P0 | ✅ |
| N-04-04 | Grounding validator | `scripts/dataset/grounding.py` | P0 | ✅ |
| N-04-05 | Paraphrase pass | `scripts/dataset/paraphrase.py` | P1 | ⏸ Deferred (template variants suffice) |
| N-04-06 | Train/val split | `scripts/dataset/split.py` | P0 | ✅ |
| N-04-07 | Manual review sample | `data/datasets/manual_review/` | P0 | ✅ |
| N-04-08 | Dataset stats report | `data/datasets/stats.json` | P1 | ✅ |

---

## 1. Templates (N-04-01)

- [x] Template categories per README strategy table
- [x] PT-BR templates with `{food_name}`, `{nutrient}`, `{value}`, `{unit}` placeholders
- [x] EN templates (minority) for multilingual robustness
- [x] Comparison templates: require two food records
- [x] Portion templates: `{portion_g}` multiplier logic
- [x] Allergen templates: require OFF records with `ingredients_text`
- [x] Minimum 5 template variants per category

---

## 2. Answer generator (N-04-02)

- [x] Function `generate_answer(record, template_type, params) -> str`
- [x] Format numbers: 1 decimal for macros, integer for kcal
- [x] Always include source citation: TACO (NEPA/UNICAMP), USDA FDC, Open Food Facts
- [x] Comparison answers: state both values + winner
- [x] Portion answers: scale from 100g basis correctly
- [x] Never include nutrients that are null in source

---

## 3. Generation pipeline (N-04-03)

- [x] Iterate TACO records — generate ~800–1500 examples (oversample)
- [x] Iterate FDC Foundation sample — ~500 examples
- [x] Iterate OFF Brazil sample — ~500–1000 examples (allergen + branded)
- [x] Generate comparison pairs from same category
- [x] Output raw: `data/datasets/raw_generated.jsonl`
- [x] Log per example: `{example_id, source_record_id, template_id, params}`

---

## 4. Grounding validator (N-04-04)

- [x] Parse assistant answer — extract numeric claims
- [x] Cross-check against source record in `foods.parquet`
- [x] Fail if kcal/macros differ by > 2% from source (rounding tolerance)
- [x] Fail if source citation missing
- [x] Reject and log failed examples — do not include in train/val
- [x] Target: 100% pass rate on final dataset

**Result:** 3000/3000 pass (100%)

---

## 5. Paraphrase pass (N-04-05)

- [ ] Take 30–50% of questions — generate 2–3 paraphrases each
- [ ] Options: local Qwen via Ollama, or one-time API batch
- [ ] Keep same answer — only question varies
- [ ] Deduplicate near-identical questions (cosine > 0.95)

Deferred — 33 template variants provide sufficient question diversity for v1.

---

## 6. Train/val split (N-04-06)

- [x] 90/10 split — stratify by template category
- [x] Ensure same food not in both train and val (group split by food id)
- [x] Output: `train.jsonl`, `val.jsonl`
- [x] Shuffle train set

**Result:** train=2702 · val=298

---

## 7. Manual review (N-04-07)

- [x] Sample 200 examples (or 10%) → `manual_review/sample_200.jsonl`
- [x] Review checklist:
  - [x] Natural Portuguese?
  - [x] Factually correct?
  - [x] Source cited?
  - [x] Appropriate tone for nutrition app?
- [x] Document issues + fix or remove bad examples
- [x] Sign-off note in `manual_review/REVIEW.md`

---

## 8. Stats report (N-04-08)

- [x] `stats.json`: total examples, per-template counts, per-source counts, avg answer length
- [x] Token count estimate (tokenizer from base model)
- [x] Confirm avg + max sequence fits training config (≤ 2048 tokens)

**Result:** avg ~132 tokens · max ~191 tokens

---

## Gate

- [x] ≥ 2,000 train examples
- [x] Grounding validator 100% pass
- [x] Manual review sign-off
- [x] Ready for [Phase 5](../05-finetuning-training/TASKS.md)

**Effort estimate:** 7–10 days
