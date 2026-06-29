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
export NUTRI_ADAPTER=nutri-qwen25-3b-v1
export NUTRI_GGUF_QUANT=q4_k_m
python scripts/export/run_all.py --skip-merge
python scripts/inference/run_all.py --skip-export
./scripts/validate-nutri-inference.sh

# Production setup (RAG v2 index + v1 GGUF + embedder A/B)
cd nutri-offline && bash scripts/production/setup_production.sh
./scripts/validate-nutri-production.sh   # v2 index metadata + golden G1–G5 + GGUF path

# Offline assistant (Phase 7 + RAG V2 lookup)
bash scripts/app/start_chat.sh          # llama-server + chat UI at http://127.0.0.1:8090/
python scripts/app/nutri_cli.py ask "arroz 100g"    # lookup path (~90 ms, no LLM)
python scripts/app/nutri_cli.py ask "Quantas calorias tem banana prata?"
./scripts/validate-nutri-app.sh
./scripts/validate-nutri-rag-v2.sh   # RAG V2 alias + hybrid + cache + benchmark gate

# RAG V2 benchmarks (optional)
# cd nutri-offline && python scripts/app/benchmark_v2.py --skip-llm
# cd nutri-offline && python scripts/rag/embedder_benchmark.py --device cpu
# Mobile pack ≤200 MB (Phase 8)
cd nutri-offline && source venv/bin/activate && export HF_HOME="$(pwd)/models/base"
python scripts/mobile/select_mobile_records.py
python scripts/mobile/build_mobile_index.py --device cuda
python scripts/mobile/build_mobile_lexicon.py
python scripts/mobile/export_embedder_onnx.py
python scripts/mobile/build_pack.py
./scripts/validate-nutri-mobile-pack.sh
python scripts/mobile/benchmark_mobile_parity.py
python scripts/app/nutri_cli.py ask "arroz 100g" --runtime mobile
```

Run gate scripts from the **repository root** (they `cd` into `nutri-offline/` automatically).

## Documentation

| Document | Purpose |
|----------|---------|
| [nutri-offline/README.md](../nutri-offline/README.md) | Project entry point |
| [nutri-offline/IMPLEMENTATION-PLAN.md](../nutri-offline/IMPLEMENTATION-PLAN.md) | Master roadmap (phases 0–8) |
| [nutri-offline/ENVIRONMENT.md](../nutri-offline/ENVIRONMENT.md) | Pinned versions and reproduce steps |
| [nutri-offline/phases/](../nutri-offline/phases/) | Per-phase README + TASKS checklists |
| [nutri-offline/docs/README-RAG-V2.md](../nutri-offline/docs/README-RAG-V2.md) | RAG V2 — speed, accuracy, shorthand UX |
| [nutri-offline/docs/MOBILE-CAPABILITY-MATRIX.md](../nutri-offline/docs/MOBILE-CAPABILITY-MATRIX.md) | Desktop parity at ≤200 MB |
| [nutri-offline/phases/08-mobile-pack/](../nutri-offline/phases/08-mobile-pack/) | Mobile pack tasks |
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
| [scripts/validate-nutri-rag-v2.sh](../scripts/validate-nutri-rag-v2.sh) | RAG V2 |
| [scripts/validate-nutri-production.sh](../scripts/validate-nutri-production.sh) | Production |
| [scripts/validate-nutri-mobile-pack.sh](../scripts/validate-nutri-mobile-pack.sh) | Phase 8 (planned) |
