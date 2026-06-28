# Phase 5 tasks — Fine-tuning training

> **ID:** N-05 · Unsloth QLoRA SFT  
> **Quality gate:** Training completes; domain eval targets met; adapter saved  
> **Status:** In progress — **Block B + C (ci smoke) done** · full training pending  
> **Depends on:** [Phase 0](../00-hardware-environment/TASKS.md), [Phase 4](../04-finetuning-dataset/TASKS.md)

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [A — Prerequisites](TRAINING-READINESS.md#block-a--prerequisites-verification-no-new-code) | Verify Phases 0–4 locally | ✅ Validated via preflight gate |
| [B — Implementation](TRAINING-READINESS.md#block-b--implementation-required-before-training) | Build `scripts/training/` | ✅ Done |
| [C — Pre-flight](TRAINING-READINESS.md#block-c--pre-flight-manual-15-min) | Mini-train 2 steps, no OOM | ✅ ci profile — peak 2.89 GB VRAM |
| [D — Full training](TRAINING-READINESS.md#block-d--full-training-run-execution) | 3 epochs → adapter | ⬜ Next step |
| [E — Post-train](TRAINING-READINESS.md#block-e--post-train-validation-phase-5-complete-not-blocking-ready-to-train) | Eval, GGUF re-export | ⬜ Blocked on D |

---

## Owner decisions (resolved 2026-06-28)

| Decision | Choice | Status |
|----------|--------|--------|
| **Base model** | `unsloth/Qwen2.5-3B-Instruct-bnb-4bit` | ✅ |
| **Epochs** | 3 | ✅ |
| **max_seq_length** | 2048 | ✅ |
| **lora_r / lora_alpha** | 16 / 32 | ✅ |
| **Early stopping** | Yes — patience 3 on val loss | ✅ |
| **Output adapter** | `models/adapters/nutri-qwen25-3b-v1/` | ✅ |

---

## 0. Prerequisites (Phase 4 + Phase 0)

| Check | Status |
|-------|--------|
| Phase 0 smoke train passed | ✅ |
| Phase 4 `train.jsonl`, `val.jsonl` | ✅ (~2,702 / ~298) |
| `stats.json` max tokens ≤ 2048 | ✅ ~191 tokens |
| Hugging Face token (if gated model) | ✅ Not required |
| `scripts/training/` implemented | ✅ |

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-05-01 | Training config | `scripts/training/config.yaml` | P0 | ✅ |
| N-05-02 | Dataset loader (ChatML) | `scripts/training/dataset_loader.py` | P0 | ✅ |
| N-05-03 | Unsloth SFT train script | `scripts/training/train_qlora.py` | P0 | ✅ |
| N-05-04 | Run training (3 epochs) | `models/adapters/nutri-qwen25-3b-v1/` | P0 | ⬜ |
| N-05-05 | Training metrics log | `logs/training-run-*.json` | P0 | ⬜ (ci smoke logged) |
| N-05-06 | Domain evaluation | `scripts/training/eval_domain.py` | P0 | ⬜ |
| N-05-07 | Base vs fine-tuned comparison | `scripts/training/compare_base_vs_ft.py` | P1 | ⬜ |
| N-05-08 | Iterate if quality insufficient | adjust epochs / lr / data | P1 | ⬜ |
| N-05-10 | Training paths module | `scripts/training/_paths.py` | P0 | ✅ |
| N-05-11 | Preflight validator | `scripts/training/preflight.py` | P0 | ✅ |
| N-05-12 | Orchestrator | `scripts/training/run_all.py` | P1 | ✅ |
| N-05-13 | Unit tests | `tests/test_dataset_loader.py` | P0 | ✅ |
| N-05-14 | Repo preflight gate | `scripts/validate-nutri-training-preflight.sh` | P0 | ✅ |
| N-05-15 | Docs update | `docs/nutri-offline.md` | P1 | ✅ |
| N-05-16 | System prompt alignment | `constants.SYSTEM_PROMPT` import | P0 | ✅ |
| N-05-17 | Post-train gate | `scripts/validate-nutri-training.sh` | P0 | ⬜ |
| N-05-18 | Re-export GGUF after train | Phase 6 with `nutri-qwen25-3b-v1` | P0 | ⬜ |

Readiness-only tasks (N-05-R01 … R15): see [TRAINING-READINESS.md](TRAINING-READINESS.md).

---

## 1. Config (N-05-01)

- [x] YAML with all hyperparameters from [README.md](README.md)
- [x] Paths: train/val jsonl, output dir, base model id
- [x] Reproducibility: `seed: 42`
- [x] `ci` profile for 2-step smoke (quantun-ia profile pattern)

---

## 2. Dataset loader (N-05-02)

- [x] Load JSONL ChatML format
- [x] Convert to HuggingFace `Dataset` with formatted text column
- [x] Apply chat template from Qwen2.5 tokenizer
- [x] Verify tokenized sample length — flag examples > max_seq_length
- [x] Filter oversized examples (log count removed)

---

## 3. Train script (N-05-03)

- [x] Load base model with Unsloth `FastLanguageModel.from_pretrained` (4-bit)
- [x] Apply LoRA: r=16, alpha=32, target_modules from config
- [x] TRL `SFTTrainer` with config from yaml
- [x] Enable fp16, paged_adamw_8bit
- [x] Eval on val set every N steps (full profile)
- [x] Save adapter + tokenizer
- [x] Gradient checkpointing via Unsloth
- [x] `--profile ci` and `--max-steps` for Block C mini-train

---

## 4. Run training (N-05-04)

- [x] Pre-flight: Block C ci smoke passed (2 steps, 2.89 GB peak VRAM)
- [ ] Run full: `python scripts/training/train_qlora.py --config scripts/training/config.yaml`
- [ ] Monitor VRAM peak during full run
- [ ] Save final adapter to `models/adapters/nutri-qwen25-3b-v1/`

---

## 5. Metrics log (N-05-05)

- [x] Log train loss per step (ci smoke)
- [x] Save `logs/training-run-{timestamp}.json`
- [ ] Confirm no loss divergence over full 3 epochs

---

## 6. Domain evaluation (N-05-06)

- [ ] Curated eval set: 50 prompts (not in train set)
- [ ] Metrics: source citation, numeric accuracy, hallucination on unknown food
- [ ] Output: `logs/eval-domain-{timestamp}.json`
- [ ] Pass criteria per README targets

---

## 7. Comparison (N-05-07)

- [ ] Same 20 prompts — base model vs fine-tuned
- [ ] Side-by-side markdown report: `logs/comparison-report.md`

---

## 8. Iteration (N-05-08)

If eval fails:
- [ ] More TACO examples in dataset (Phase 4 revisit)
- [ ] +1 epoch or lower LR (1e-4)
- [ ] Try lora_r=32 if underfitting
- [ ] Document experiment matrix in `logs/experiments.md`

---

## Gate

- [x] **Ready to train:** Blocks A + B + C complete
- [ ] Training completed without OOM (full 3 epochs)
- [ ] Domain eval meets targets
- [ ] Adapter `nutri-qwen25-3b-v1` saved and loadable
- [ ] Ready for [Phase 6](../06-gguf-inference/TASKS.md) with `NUTRI_ADAPTER=nutri-qwen25-3b-v1`

**Next command:**

```bash
cd nutri-offline && source venv/bin/activate
export HF_HOME="$(pwd)/models/base" UNSLOTH_USE_FP16=1
python scripts/training/train_qlora.py --config scripts/training/config.yaml
```

---

## Optional follow-up (post-v1)

| Task | When |
|------|------|
| Scale to Qwen2.5-7B | After 3B pipeline proven |
| DPO on preference pairs | If SFT tone wrong but facts OK |
| Merge LoRA into base | Before GGUF if llama.cpp path requires merged weights |
