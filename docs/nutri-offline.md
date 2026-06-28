# NutriOffline — ML pipeline

The **NutriOffline** pipeline trains a small nutrition LLM with QLoRA and builds an offline vector RAG index. Source code and documentation live in [`nutri-offline/`](../nutri-offline/). Heavy artifacts (datasets, models, venv) are **gitignored** inside that directory.

OpenFitness Android integration is documented for a future phase — see [nutri-offline/docs/android-integration.md](../nutri-offline/docs/android-integration.md).

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

# Environment setup
cd nutri-offline
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export HF_HOME="$(pwd)/models/base"
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

# QLoRA training (Phase 5)
./scripts/validate-nutri-training-preflight.sh
cd nutri-offline && source venv/bin/activate
export HF_HOME="$(pwd)/models/base" UNSLOTH_USE_FP16=1
python scripts/training/train_qlora.py --config scripts/training/config.yaml --profile ci   # 2-step smoke
python scripts/training/train_qlora.py --config scripts/training/config.yaml               # full 3 epochs

# GGUF export + inference (Phase 6)
export NUTRI_ADAPTER=smoke-test
python scripts/export/run_all.py --skip-merge
python scripts/inference/run_all.py --skip-export
./scripts/validate-nutri-inference.sh

# Offline assistant (Phase 7)
bash scripts/app/start_offline.sh
python scripts/app/nutri_cli.py ask "Quantas calorias tem banana prata?"
./scripts/validate-nutri-app.sh
```

Run gate scripts from the **repository root** (they `cd` into `nutri-offline/` automatically).

## Documentation

| Document | Purpose |
|----------|---------|
| [nutri-offline/README.md](../nutri-offline/README.md) | Project entry point |
| [nutri-offline/IMPLEMENTATION-PLAN.md](../nutri-offline/IMPLEMENTATION-PLAN.md) | Master roadmap (phases 0–7) |
| [nutri-offline/ENVIRONMENT.md](../nutri-offline/ENVIRONMENT.md) | Pinned versions and reproduce steps |
| [nutri-offline/phases/](../nutri-offline/phases/) | Per-phase README + TASKS checklists |
| [nutri-offline/docs/UC-nutri-query.md](../nutri-offline/docs/UC-nutri-query.md) | Use case draft |
| [nutri-offline/docs/android-integration.md](../nutri-offline/docs/android-integration.md) | Android integration options |

## Architecture

```
User question → local embedding → vector DB (top-k)
                                      ↓
              fine-tuned LLM (GGUF, llama.cpp) → natural-language answer
```

Fine-tuning teaches reasoning and Brazilian Portuguese tone; **factual macros come from RAG**, not model memory.

## Quality gates

| Script | Phase |
|--------|-------|
| [scripts/validate-nutri-hardware.sh](../scripts/validate-nutri-hardware.sh) | N-00 |
| [scripts/validate-nutri-data-acquisition.sh](../scripts/validate-nutri-data-acquisition.sh) | N-01 |
| [scripts/validate-nutri-normalization.sh](../scripts/validate-nutri-normalization.sh) | N-02 |
| [scripts/validate-nutri-rag.sh](../scripts/validate-nutri-rag.sh) | N-03 |
| [scripts/validate-nutri-dataset.sh](../scripts/validate-nutri-dataset.sh) | N-04 |
| [scripts/validate-nutri-training-preflight.sh](../scripts/validate-nutri-training-preflight.sh) | N-05 |
| [scripts/validate-nutri-inference.sh](../scripts/validate-nutri-inference.sh) | N-06 |
| [scripts/validate-nutri-app.sh](../scripts/validate-nutri-app.sh) | N-07 |
