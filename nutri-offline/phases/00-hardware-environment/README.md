# Phase 0 — Hardware validation & training environment

> **Status:** Done (2026-06-27)  
> **Parent:** [IMPLEMENTATION-PLAN.md](../../IMPLEMENTATION-PLAN.md)  
> **Goal:** Confirm RTX 4060 8 GB is ready for QLoRA; install CUDA, PyTorch, Unsloth stack on Pop!_OS 24.04.

---

## Objective

Validate the local machine meets minimum requirements for QLoRA fine-tuning of 1B–8B models and establish a reproducible Python environment isolated from the OpenFitness Android/Kotlin codebase.

| Check | Target |
|-------|--------|
| GPU VRAM | ≥ 8 GB (RTX 4060 Laptop) |
| CUDA | Compatible with PyTorch + Unsloth |
| RAM | 31 GiB — sufficient for DuckDB + dataset loading |
| Disk | ≥ 100 GB free for datasets, checkpoints, GGUF |
| OS | Pop!_OS 24.04 — native CUDA, no WSL |

---

## Hardware profile (confirmed)

| Component | Spec | Implication |
|-----------|------|-------------|
| CPU | Intel Core i7-13620H (13th gen) | Preprocessing, CPU embeddings fallback, vector indexing |
| GPU | NVIDIA RTX 4060 Laptop (8 GB) | QLoRA for 1B–8B; full fine-tuning out of scope |
| RAM | 31 GiB | Large datasets in DuckDB without swap pressure |
| Disk | 1.35 TiB | Room for OFF dump, FDC bulk, checkpoints |
| OS | Pop!_OS 24.04 (Linux, Wayland) | CUDA + PyTorch native |

**Conclusion:** 8 GB VRAM is the minimum viable floor for QLoRA. Start with Qwen2.5-3B; scale to 7–8B only after pipeline validation.

---

## Target directory layout

```
nutri-offline/
├── venv/                    # Python 3.12 virtualenv
├── data/
│   ├── raw/                 # downloaded sources
│   ├── processed/           # normalized parquet/csv
│   └── datasets/            # fine-tuning jsonl
├── models/
│   ├── base/                # Hugging Face cache
│   ├── adapters/            # LoRA checkpoints
│   └── gguf/                # exported inference weights
├── indexes/                 # LanceDB / sqlite-vec
└── scripts/                 # download, normalize, train, eval
```

---

## Out of scope

| Item | Reason |
|------|--------|
| Full fine-tuning (FFT) of 7B+ | Requires 60–80 GB VRAM |
| Cloud GPU rental | Project goal is 100% local |
| Integration with `:domain` Kotlin modules | ML pipeline is separate until Phase 7 |

---

## Definition of done

- [x] `nvidia-smi` shows RTX 4060 with ≥ 7.5 GB usable VRAM
- [x] PyTorch sees CUDA: `torch.cuda.is_available() == True`
- [x] Unsloth imports and runs a 10-step smoke train on Qwen2.5-3B without OOM (peak 2.89 GB)
- [x] `nutri-offline/` directory structure created
- [x] `requirements.txt` / `requirements-lock.txt` pinned and documented in `ENVIRONMENT.md`

**Smoke train log:** `nutri-offline/logs/smoke-train.log`  
**Tracked repo docs:** [docs/nutri-offline-local.md](../../../docs/nutri-offline-local.md)

---

**References:** [TASKS.md](TASKS.md) · [Unsloth RTX 4060 profiling](https://unsloth.ai/docs)
