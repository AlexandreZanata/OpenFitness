# Phase 5 — Fine-tuning training (Unsloth QLoRA)

> **Status:** Done — adapter trained; post-train eval + gate implemented (2026-06-29)  
> **Parent:** [Phase 4](../04-finetuning-dataset/README.md) · [Phase 0](../00-hardware-environment/README.md)  
> **Goal:** Real QLoRA supervised fine-tuning of Qwen2.5-3B-Instruct on the nutrition dataset.

---

## Objective

Train LoRA adapters that teach the base model Brazilian nutrition terminology, response format, source citation habit, and portion/comparison reasoning. **Not** to memorize food tables — RAG handles facts.

---

## Base model candidates

| Model | Params | VRAM (QLoRA train) | Notes |
|-------|--------|-------------------|-------|
| **Qwen2.5-3B-Instruct** | 3B | ~5–6 GB | **Start here** — strong PT-BR, fast iteration |
| Qwen3-4B-Instruct | 4B | ~6 GB | Alternative if available |
| Llama 3.2 3B Instruct | 3B | ~6 GB | Good instruction following |
| Qwen2.5-7B / Llama 3.1 8B | 7–8B | ~7–8 GB (limit) | Scale up after pipeline validated |

---

## Training configuration

```yaml
method: QLoRA (4-bit NF4)
base_model: Qwen/Qwen2.5-3B-Instruct
lora_r: 16
lora_alpha: 32
target_modules: all-linear
batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 2.0e-4
num_epochs: 3
max_seq_length: 2048
optimizer: paged_adamw_8bit
precision: fp16          # avoid bf16 on RTX 4060
warmup_ratio: 0.05
weight_decay: 0.01
lr_scheduler: cosine
save_steps: 100
eval_steps: 100
```

**RTX 4060 notes:** batch 1–2 max; fp16 + PagedAdamW most efficient; monitor VRAM with `nvidia-smi -l 1`.

---

## Training script layout

```
scripts/training/
├── train_qlora.py         # Unsloth SFT main script
├── config.yaml            # hyperparameters + ci/full profiles
├── config_loader.py       # profile merge (quantun-ia pattern)
├── dataset_loader.py      # Phase 4 ChatML → SFT text
├── preflight.py           # CUDA/disk/dataset gate
├── run_all.py             # preflight → train orchestrator
├── eval_domain.py         # domain-specific eval (50 prompts)
├── eval_scoring.py        # pure scoring logic (unit-tested)
├── training_metrics.py    # loss stability from training-run JSON
└── compare_base_vs_ft.py  # qualitative comparison report

models/adapters/
└── nutri-qwen25-3b-v1/    # LoRA checkpoint
```

---

## Evaluation criteria

| Metric | Method | Target |
|--------|--------|--------|
| Validation loss | TRL eval loop | Stable decrease, no divergence |
| Format compliance | Regex: cites source, includes numbers when asked | ≥ 90% |
| Hallucination rate | Ask for food NOT in context — should say unknown | ≤ 10% false facts |
| RAG fidelity | Answer with RAG context injected — numbers match context | ≥ 95% |
| PT-BR quality | Manual review 50 prompts | Subjective pass |

---

## Out of scope

| Item | Reason |
|------|--------|
| Full fine-tuning (FFT) | 60–80 GB VRAM for 7B |
| DPO / RLHF | Follow-up if SFT quality insufficient |
| Multi-GPU | Single RTX 4060 only |

---

## Definition of done

- [x] Training completes 3 epochs without OOM
- [x] Validation loss plotted and stable
- [x] Domain eval gate passes (format citation + RAG fidelity)
- [x] LoRA adapter saved to `models/adapters/nutri-qwen25-3b-v1/`
- [x] Qualitative comparison: fine-tuned vs base shows clear domain improvement
- [x] Ready for [Phase 6 — GGUF export](../06-gguf-inference/TASKS.md)

**Known gap (N-05-08):** Without RAG context, the model may invent TACO values for fictional foods (~80% hallucination on the 50-prompt unknown subset). Production relies on RAG for facts.

---

**References:** [TASKS.md](TASKS.md) · [Unsloth docs](https://unsloth.ai/docs) · [PEFT](https://github.com/huggingface/peft) · [TRL SFT](https://huggingface.co/docs/trl/sft_trainer)
