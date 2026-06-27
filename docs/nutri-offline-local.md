# NutriOffline — local ML pipeline (gitignored)

The **NutriOffline** pipeline trains a small nutrition LLM with QLoRA and builds an offline vector RAG index. It lives entirely under `.local/` and is **not committed to git** (datasets, checkpoints, venv, Hugging Face cache).

OpenFitness v1 (Android) remains separate until [Phase 7](.local/phases/07-app-integration/README.md).

## Hardware baseline

| Component | Minimum |
|-----------|---------|
| GPU | NVIDIA ≥ 8 GB VRAM (validated: RTX 4060 Laptop) |
| RAM | ≥ 16 GiB (31 GiB recommended for DuckDB) |
| Disk | ≥ 100 GB free for datasets and checkpoints |
| OS | Linux with proprietary NVIDIA drivers (Pop!_OS 24.04 tested) |

## Quick start

```bash
# GPU gate (no Python required)
./scripts/validate-nutri-hardware.sh

# Full environment (after Phase 0 setup)
cd .local/nutri-offline
source venv/bin/activate
python scripts/validate_environment.py
python scripts/smoke_train.py

# Data acquisition (Phase 1)
python scripts/download/run_all.py
./scripts/validate-nutri-data-acquisition.sh
```

## Local documentation

All NutriOffline docs are under `.local/`:

| Document | Purpose |
|----------|---------|
| [.local/IMPLEMENTATION-PLAN.md](../.local/IMPLEMENTATION-PLAN.md) | Master roadmap (phases 0–7) |
| [.local/nutri-offline/ENVIRONMENT.md](../.local/nutri-offline/ENVIRONMENT.md) | Pinned versions and reproduce steps |
| [.local/phases/00-hardware-environment/TASKS.md](../.local/phases/00-hardware-environment/TASKS.md) | Phase 0 task checklist |
| [.local/phases/01-data-acquisition/TASKS.md](../.local/phases/01-data-acquisition/TASKS.md) | Phase 1 task checklist |

## Architecture (target)

```
User question → local embedding → vector DB (top-k)
                                      ↓
              fine-tuned LLM (GGUF, llama.cpp) → natural-language answer
```

Fine-tuning teaches reasoning and Brazilian Portuguese tone; **factual macros come from RAG**, not model memory.

## Repo scripts

| Script | Purpose |
|--------|---------|
| [scripts/validate-nutri-hardware.sh](../scripts/validate-nutri-hardware.sh) | Gate N-00-01 — NVIDIA GPU + VRAM check |
| [scripts/validate-nutri-data-acquisition.sh](../scripts/validate-nutri-data-acquisition.sh) | Gate N-01-08 — raw data smoke read |
