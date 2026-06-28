# Phase 5 tasks — Fine-tuning training

> **ID:** N-05 · Unsloth QLoRA SFT  
> **Quality gate:** Training completes; domain eval targets met; adapter saved  
> **Status:** Not started  
> **Depends on:** [Phase 0](../00-hardware-environment/TASKS.md), [Phase 4](../04-finetuning-dataset/TASKS.md)

---

## Owner decisions (resolve before N-05-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Base model** | Qwen2.5-3B-Instruct (recommended) · Qwen3-4B · Llama 3.2 3B | ⬜ |
| **Epochs** | 2 · 3 (recommended) · 4 | ⬜ |
| **max_seq_length** | 1024 · 2048 (recommended) · 512 if OOM | ⬜ |
| **lora_alpha** | 16 · 32 (recommended) | ⬜ |
| **Early stopping** | Yes on val loss plateau · No | ⬜ |

---

## 0. Prerequisites

- [ ] Phase 0 smoke train passed
- [ ] Phase 4 dataset: `train.jsonl`, `val.jsonl` ready
- [ ] Hugging Face token configured (if model gated)
- [ ] Close other GPU processes (browser, etc.) before training

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-05-01 | Training config | `scripts/training/config.yaml` | P0 | ⬜ |
| N-05-02 | Dataset loader (ChatML) | `scripts/training/dataset_loader.py` | P0 | ⬜ |
| N-05-03 | Unsloth SFT train script | `scripts/training/train_qlora.py` | P0 | ⬜ |
| N-05-04 | Run training (3 epochs) | `models/adapters/nutri-qwen25-3b-v1/` | P0 | ⬜ |
| N-05-05 | Training metrics log | `logs/training-run-*.json` | P0 | ⬜ |
| N-05-06 | Domain evaluation | `scripts/training/eval_domain.py` | P0 | ⬜ |
| N-05-07 | Base vs fine-tuned comparison | `scripts/training/compare_base_vs_ft.py` | P1 | ⬜ |
| N-05-08 | Iterate if quality insufficient | adjust epochs / lr / data | P1 | ⬜ |

---

## 1. Config (N-05-01)

- [ ] YAML with all hyperparameters from README
- [ ] Paths: train/val jsonl, output dir, base model id
- [ ] Reproducibility: `seed: 42`
- [ ] Document expected VRAM and runtime in config comments

---

## 2. Dataset loader (N-05-02)

- [ ] Load JSONL ChatML format
- [ ] Convert to HuggingFace `Dataset` with `messages` column
- [ ] Apply chat template from Qwen2.5 tokenizer
- [ ] Verify tokenized sample length — flag examples > max_seq_length
- [ ] Filter or truncate oversized examples (log count removed)

---

## 3. Train script (N-05-03)

- [ ] Load base model with Unsloth `FastLanguageModel.from_pretrained` (4-bit)
- [ ] Apply LoRA: r=16, alpha=32, target_modules=all-linear
- [ ] TRL `SFTTrainer` with config from yaml
- [ ] Enable fp16, paged_adamw_8bit
- [ ] Eval on val set every N steps
- [ ] Save best adapter by val loss
- [ ] Gradient checkpointing if VRAM tight

Reference pattern:

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(model, r=16, ...)
```

---

## 4. Run training (N-05-04)

- [ ] Pre-flight: `nvidia-smi` — confirm ≥ 7 GB free VRAM
- [ ] Run: `python scripts/training/train_qlora.py --config scripts/training/config.yaml`
- [ ] Monitor VRAM peak — if OOM:
  - [ ] Reduce max_seq_length to 1024
  - [ ] Reduce batch to 1, increase grad_accum
  - [ ] Reduce lora_r to 8
- [ ] Expected runtime: 1–4 hours per epoch (2k–5k examples, 3B model)
- [ ] Save final adapter + tokenizer to `models/adapters/nutri-qwen25-3b-v1/`

---

## 5. Metrics log (N-05-05)

- [ ] Log train loss, val loss per step/epoch
- [ ] Save `logs/training-run-{timestamp}.json`
- [ ] Optional: tensorboard or wandb (local only — no cloud required)
- [ ] Plot loss curve — confirm no divergence

---

## 6. Domain evaluation (N-05-06)

- [ ] Curated eval set: 50 prompts (not in train set)
  - 20 direct lookup (TACO foods)
  - 10 comparison
  - 10 portion math
  - 10 "unknown food" (should not hallucinate)
- [ ] Metrics:
  - [ ] Source citation present (regex)
  - [ ] Numeric accuracy vs ground truth
  - [ ] Hallucination on unknown food
- [ ] Run with RAG context injected (simulate Phase 7)
- [ ] Output: `logs/eval-domain-{timestamp}.json`
- [ ] Pass criteria per README targets

---

## 7. Comparison (N-05-07)

- [ ] Same 20 prompts — base model vs fine-tuned
- [ ] Side-by-side markdown report: `logs/comparison-report.md`
- [ ] Fine-tuned should show: better PT-BR, source citation, nutrition terminology

---

## 8. Iteration (N-05-08)

If eval fails:
- [ ] More TACO examples in dataset (Phase 4 revisit)
- [ ] +1 epoch or lower LR (1e-4)
- [ ] Try lora_r=32 if underfitting
- [ ] Document experiment matrix in `logs/experiments.md`

---

## Gate

- [ ] Training completed without OOM
- [ ] Domain eval meets targets (or documented acceptable tradeoffs)
- [ ] Adapter saved and loadable
- [ ] Ready for [Phase 6](../06-gguf-inference/TASKS.md)

**Effort estimate:** 2–5 days (including iteration)

---

## Optional follow-up (post-v1)

| Task | When |
|------|------|
| Scale to Qwen2.5-7B | After 3B pipeline proven |
| DPO on preference pairs | If SFT tone wrong but facts OK |
| Merge LoRA into base | Before GGUF if llama.cpp path requires merged weights |
