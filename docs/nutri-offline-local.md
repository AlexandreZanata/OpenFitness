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

# Normalization (Phase 2)
python scripts/normalize/run_all.py
./scripts/validate-nutri-normalization.sh

# Vector RAG index (Phase 3)
python scripts/rag/run_all.py --scope v1 --device cuda
./scripts/validate-nutri-rag.sh

# Fine-tuning dataset (Phase 4)
python scripts/dataset/run_all.py --target 3000
./scripts/validate-nutri-dataset.sh

# GGUF export + inference (Phase 6)
export NUTRI_ADAPTER=smoke-test
python scripts/export/run_all.py --skip-merge
python scripts/inference/run_all.py --skip-export
./scripts/validate-nutri-inference.sh
```

## Local documentation

All NutriOffline docs are under `.local/`:

| Document | Purpose |
|----------|---------|
| [.local/IMPLEMENTATION-PLAN.md](../.local/IMPLEMENTATION-PLAN.md) | Master roadmap (phases 0–7) |
| [.local/nutri-offline/ENVIRONMENT.md](../.local/nutri-offline/ENVIRONMENT.md) | Pinned versions and reproduce steps |
| [.local/phases/00-hardware-environment/TASKS.md](../.local/phases/00-hardware-environment/TASKS.md) | Phase 0 task checklist |
| [.local/phases/01-data-acquisition/TASKS.md](../.local/phases/01-data-acquisition/TASKS.md) | Phase 1 task checklist |
| [.local/phases/02-data-normalization/TASKS.md](../.local/phases/02-data-normalization/TASKS.md) | Phase 2 task checklist |
| [.local/phases/03-vector-db-rag/TASKS.md](../.local/phases/03-vector-db-rag/TASKS.md) | Phase 3 task checklist |
| [.local/phases/04-finetuning-dataset/TASKS.md](../.local/phases/04-finetuning-dataset/TASKS.md) | Phase 4 task checklist |
| [.local/phases/06-gguf-inference/TASKS.md](../.local/phases/06-gguf-inference/TASKS.md) | Phase 6 task checklist |

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
| [scripts/validate-nutri-normalization.sh](../scripts/validate-nutri-normalization.sh) | Gate N-02-06 — unified schema + golden rows |
| [scripts/validate-nutri-rag.sh](../scripts/validate-nutri-rag.sh) | Gate N-03-05 — LanceDB index + acceptance queries |
| [scripts/validate-nutri-dataset.sh](../scripts/validate-nutri-dataset.sh) | Gate N-04 — ChatML dataset grounding + counts |
| [scripts/validate-nutri-inference.sh](../scripts/validate-nutri-inference.sh) | Gate N-06 — GGUF + llama-server smoke tests |
