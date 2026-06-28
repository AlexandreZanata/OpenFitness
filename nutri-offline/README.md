# NutriOffline — offline nutrition LLM + RAG

Python pipeline for QLoRA fine-tuning, vector search over TACO/FDC/Open Food Facts, and local inference via llama.cpp.

**Principle:** fine-tuning teaches reasoning and tone; **RAG supplies factual macros**.

## Quick start

From the repository root:

```bash
# Hardware gate (no Python)
./scripts/validate-nutri-hardware.sh

cd nutri-offline
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export HF_HOME="$(pwd)/models/base"
python scripts/validate_environment.py
python scripts/smoke_train.py
```

See [docs/nutri-offline.md](../docs/nutri-offline.md) for the full phase workflow and gate scripts.

## Layout

```
nutri-offline/
├── IMPLEMENTATION-PLAN.md   # Master roadmap (phases 0–7)
├── ENVIRONMENT.md           # Pinned stack and reproduce steps
├── phases/                  # Per-phase README + TASKS
├── scripts/                 # Pipeline code
├── tests/                   # Unit tests
├── docs/                    # Android guide, use case draft
├── data/                    # gitignored — raw + processed datasets
├── models/                  # gitignored — adapters, GGUF, HF cache
├── indexes/                 # gitignored — LanceDB RAG index
└── logs/                    # gitignored — run logs
```

## Phase index

| Phase | Task checklist |
|-------|----------------|
| 0 — Environment | [phases/00-hardware-environment/TASKS.md](phases/00-hardware-environment/TASKS.md) |
| 1 — Data acquisition | [phases/01-data-acquisition/TASKS.md](phases/01-data-acquisition/TASKS.md) |
| 2 — Normalization | [phases/02-data-normalization/TASKS.md](phases/02-data-normalization/TASKS.md) |
| 3 — Vector RAG | [phases/03-vector-db-rag/TASKS.md](phases/03-vector-db-rag/TASKS.md) |
| 4 — Fine-tuning dataset | [phases/04-finetuning-dataset/TASKS.md](phases/04-finetuning-dataset/TASKS.md) |
| 5 — QLoRA training | [phases/05-finetuning-training/TASKS.md](phases/05-finetuning-training/TASKS.md) |
| 6 — GGUF inference | [phases/06-gguf-inference/TASKS.md](phases/06-gguf-inference/TASKS.md) |
| 7 — App integration | [phases/07-app-integration/TASKS.md](phases/07-app-integration/TASKS.md) |

## Hardware baseline

RTX 4060 Laptop 8 GB · 31 GiB RAM · Pop!_OS 24.04 · Python 3.12
