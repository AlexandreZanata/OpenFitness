# Training readiness — tasks to 100% before first QLoRA run

> **Goal:** Everything implemented and verified so you can run  
> `python scripts/training/train_qlora.py --config scripts/training/config.yaml`  
> with confidence on RTX 4060 8 GB.  
> **Parent:** [TASKS.md](TASKS.md) · [README.md](README.md)

---

## Current status (2026-06-28)

| Area | Status | Notes |
|------|--------|-------|
| Phase 0 — env + smoke train | ✅ Done | `venv`, Unsloth, `smoke-test` adapter |
| Phase 2 — `foods.parquet` | ✅ Done | Normalization gate passes |
| Phase 4 — `train.jsonl` / `val.jsonl` | ✅ Done | ~2,702 train · ~298 val · max ~273 tok (real tokenizer) |
| Phase 5 — `scripts/training/` | ✅ Done | Block B implemented |
| Phase 5 — preflight gate | ✅ Done | `scripts/validate-nutri-training-preflight.sh` |
| Block C — ci mini-train | ✅ Done | 2 steps · peak 2.89 GB VRAM |
| Adapter `nutri-qwen25-3b-v1/` | ✅ Done | checkpoint-900 · final eval loss 0.23 |

**Bottom line:** **Ready for full training (Block D).** Run `train_qlora.py` without `--profile ci`.

---

## Owner decisions (lock before coding N-05-01)

| Decision | Recommendation | Status |
|----------|----------------|--------|
| Base model | `unsloth/Qwen2.5-3B-Instruct-bnb-4bit` (same as Phase 0) | ✅ |
| Epochs | 3 | ✅ |
| `max_seq_length` | 2048 (dataset max ~273 tok — safe) | ✅ |
| `lora_r` / `lora_alpha` | 16 / 32 | ✅ |
| Early stopping | Yes — patience 3 evals on val loss | ✅ |
| Output adapter dir | `models/adapters/nutri-qwen25-3b-v1/` | ✅ |

---

## Block A — Prerequisites verification (no new code)

Run from **repository root** unless noted.

| ID | Task | Command / check | Status |
|----|------|-----------------|--------|
| N-05-R01 | GPU gate | `./scripts/validate-nutri-hardware.sh` | ✅ |
| N-05-R02 | Dataset gate | `./scripts/validate-nutri-dataset.sh` | ✅ |
| N-05-R03 | Train/val files exist | `wc -l nutri-offline/data/datasets/{train,val}.jsonl` → ≥2000 / ≥200 | ✅ |
| N-05-R04 | Stats fit context | `nutri-offline/data/datasets/stats.json` → `max_tokens_estimate` ≤ 2048 | ✅ |
| N-05-R05 | Python stack | `cd nutri-offline && source venv/bin/activate && python scripts/validate_environment.py` | ✅ |
| N-05-R06 | Smoke train (VRAM) | `python scripts/smoke_train.py` → peak VRAM ≤ 7.5 GB | ✅ (Phase 0) |
| N-05-R07 | HF cache local | `export HF_HOME="$(pwd)/models/base"` in shell profile for session | ✅ |
| N-05-R08 | Disk space | ≥ 20 GB free under `nutri-offline/` (checkpoints + logs) | ✅ |
| N-05-R09 | GPU idle before train | Close browser/games; `nvidia-smi` ≥ 7 GB free | ⬜ (before Block D) |

**Gate A:** All ⬜ → ✅ before starting Block D.

---

## Block B — Implementation (required before training)

Create `nutri-offline/scripts/training/` and repo gate. **Nothing in this block runs multi-hour training.**

| ID | Task | Deliverable | Priority | Status |
|----|------|-------------|----------|--------|
| N-05-01 | Training config | `scripts/training/config.yaml` — paths, hyperparams, seed 42 | P0 | ✅ |
| N-05-02 | ChatML dataset loader | `scripts/training/dataset_loader.py` — load JSONL, apply Qwen chat template, filter > max_seq | P0 | ✅ |
| N-05-03 | QLoRA train script | `scripts/training/train_qlora.py` — Unsloth + TRL SFTTrainer, fp16, eval on val | P0 | ✅ |
| N-05-10 | Training paths module | `scripts/training/_paths.py` — ROOT, dataset paths, adapter output | P0 | ✅ |
| N-05-11 | Preflight validator | `scripts/training/preflight.py` — dataset token stats, CUDA, disk, config sanity | P0 | ✅ |
| N-05-12 | Orchestrator | `scripts/training/run_all.py` — preflight → train (optional `--dry-run`) | P1 | ✅ |
| N-05-13 | Unit tests | `tests/test_dataset_loader.py` — GIVEN sample JSONL WHEN load THEN chat text shape | P0 | ✅ |
| N-05-14 | Repo preflight gate | `scripts/validate-nutri-training-preflight.sh` — gates A + preflight.py (no full train) | P0 | ✅ |
| N-05-15 | Docs update | `docs/nutri-offline.md` + Phase 5 README — training commands | P1 | ✅ |
| N-05-16 | System prompt alignment | Import same `SYSTEM_PROMPT` as Phase 4 (`scripts/dataset/constants.py`) or document single source | P0 | ✅ |

### N-05-01 config.yaml (minimum fields)

```yaml
base_model: unsloth/Qwen2.5-3B-Instruct-bnb-4bit
train_jsonl: data/datasets/train.jsonl
val_jsonl: data/datasets/val.jsonl
output_dir: models/adapters/nutri-qwen25-3b-v1
max_seq_length: 2048
num_train_epochs: 3
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 2.0e-4
lora_r: 16
lora_alpha: 32
fp16: true
bf16: false
seed: 42
eval_steps: 100
save_steps: 100
logging_steps: 10
```

### N-05-02 loader acceptance

- [ ] Reads `{"messages": [...]}` from Phase 4 JSONL
- [ ] Formats with `tokenizer.apply_chat_template(..., tokenize=False)`
- [ ] Drops or logs examples exceeding `max_seq_length` after tokenization
- [ ] Logs: train count, val count, dropped count, max token length seen

### N-05-03 train script acceptance

- [ ] Matches Phase 0 patterns (`UNSLOTH_USE_FP16=1`, `HF_HOME`, 4-bit load)
- [ ] Saves adapter + tokenizer to `output_dir`
- [ ] Writes `logs/training-run-{timestamp}.json` (loss history)
- [ ] Handles OOM with clear message (suggest 1024 seq / grad_accum)

**Gate B:** N-05-01 … N-05-03, N-05-11, N-05-13, N-05-14 all ✅ → ready for Block C.

---

## Block C — Pre-flight (manual, ~15 min)

After Block B is merged locally:

```bash
cd nutri-offline
source venv/bin/activate
export HF_HOME="$(pwd)/models/base"
export UNSLOTH_USE_FP16=1

# From repo root
./scripts/validate-nutri-training-preflight.sh

# Dry-run: load model + tokenize full dataset without training
python scripts/training/preflight.py --config scripts/training/config.yaml
python scripts/training/train_qlora.py --config scripts/training/config.yaml --max-steps 2
```

| ID | Task | Expected | Status |
|----|------|----------|--------|
| N-05-R10 | Preflight gate passes | Exit 0 | ✅ |
| N-05-R11 | 2-step mini-train | No OOM; adapter dir writable | ✅ |
| N-05-R12 | Peak VRAM logged | ≤ 7.5 GB on 2-step run (2.89 GB observed) | ✅ |
| N-05-R13 | Val eval step works | Skipped in ci profile (max_steps=2); enabled in full profile | ⬜ |

**Gate C:** All ✅ → proceed to Block D (full training).

---

## Block D — Full training run (execution)

| ID | Task | Notes | Status |
|----|------|-------|--------|
| N-05-04 | Run 3 epochs | `python scripts/training/train_qlora.py --config scripts/training/config.yaml` | ⬜ |
| N-05-05 | Metrics log | `logs/training-run-*.json` — train/val loss stable | ⬜ |
| N-05-R14 | Monitor session | `watch -n 1 nvidia-smi` — note peak VRAM | ⬜ |
| N-05-R15 | Runtime note | Expect ~1–4 h per epoch (2.7k examples, RTX 4060) | ⬜ |

**OOM fallback order:**

1. `max_seq_length: 1024`
2. `gradient_accumulation_steps: 16`
3. `lora_r: 8`

---

## Block E — Post-train validation (Phase 5 complete, not blocking “ready to train”)

| ID | Task | Deliverable | Priority | Status |
|----|------|-------------|----------|--------|
| N-05-06 | Domain eval | `scripts/training/eval_domain.py` + 50 prompt suite | P0 | ✅ |
| N-05-07 | Base vs FT comparison | `scripts/training/compare_base_vs_ft.py` → `logs/comparison-report.md` | P1 | ✅ |
| N-05-08 | Iteration if needed | `logs/experiments.md` | P1 | ⬜ unknown-food hallucination |
| N-05-17 | Training gate (post-train) | `scripts/validate-nutri-training.sh` — adapter exists + eval pass | P0 | ✅ |
| N-05-18 | Re-export GGUF | `NUTRI_ADAPTER=nutri-qwen25-3b-v1 python scripts/export/run_all.py --skip-merge` | P0 | ✅ |
| N-05-19 | Mark Phase 5 TASKS Done | Update [TASKS.md](TASKS.md) + [README.md](README.md) | P1 | ✅ |

---

## Quick command reference (after Block B)

```bash
# 1. Preflight (repo root)
./scripts/validate-nutri-training-preflight.sh

# 2. Full training
cd nutri-offline
source venv/bin/activate
export HF_HOME="$(pwd)/models/base"
export UNSLOTH_USE_FP16=1
python scripts/training/train_qlora.py --config scripts/training/config.yaml

# 3. After training — export for inference
export NUTRI_ADAPTER=nutri-qwen25-3b-v1
python scripts/export/run_all.py --skip-merge
```

---

## Definition of “100% ready to train”

You are ready when **all** are true:

- [x] Block A — prerequisites verified (N-05-R01 … R08)
- [x] Block B — training code exists and tests pass (N-05-01 … 03, 11, 13, 14)
- [x] Block C — preflight + 2-step mini-train without OOM (N-05-R10 … R12)
- [x] Owner decisions table signed off

You are **Phase 5 complete** when Block D + Block E are done.

---

**Next step:** Implement Block B (estimated 1–2 days), then run Block C before leaving training unattended.
