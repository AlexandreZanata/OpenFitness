# Phase 0 tasks — Hardware & environment

> **ID:** N-00 · Environment setup  
> **Quality gate:** Unsloth smoke train completes without OOM on Qwen2.5-3B  
> **Status:** Done (2026-06-27)

---

## Owner decisions (resolve before N-00-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Python version** | 3.11 (recommended) · 3.12 | ✅ 3.12 (pyenv) |
| **Env manager** | venv (recommended) · conda · uv | ✅ venv |
| **CUDA toolkit** | System driver only (recommended) · full toolkit install | ✅ driver 580.159.03 |
| **Project root** | `nutri-offline/` (recommended) | ✅ |
| **Base model for smoke test** | Qwen2.5-3B-Instruct (recommended) | ✅ |

---

## 0. Prerequisites

- [x] Read [README.md](README.md)
- [x] Read [IMPLEMENTATION-PLAN.md](../../IMPLEMENTATION-PLAN.md) hardware section
- [x] Confirm Pop!_OS 24.04 with proprietary NVIDIA drivers installed
- [x] Confirm ≥ 100 GB free disk under `nutri-offline/` or home partition (448 GB free on /data)

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-00-01 | Verify GPU + CUDA driver | `nvidia-smi`, driver version log | P0 | ✅ |
| N-00-02 | Create Python virtualenv | `nutri-offline/venv/` | P0 | ✅ |
| N-00-03 | Install PyTorch + CUDA | pin versions in `requirements.txt` | P0 | ✅ |
| N-00-04 | Install Unsloth + deps | unsloth, peft, trl, bitsandbytes, transformers | P0 | ✅ |
| N-00-05 | Install data stack | duckdb, pandas, pyarrow, sentence-transformers | P1 | ✅ |
| N-00-06 | Create directory layout | `nutri-offline/{data,models,indexes,scripts}/` | P0 | ✅ |
| N-00-07 | Unsloth smoke train | 10 steps, Qwen2.5-3B, batch 1, log VRAM peak | P0 | ✅ |
| N-00-08 | Document environment | `ENVIRONMENT.md` with versions + reproduce steps | P1 | ✅ |

---

## 1. GPU verification (N-00-01)

- [x] Run `nvidia-smi` — capture driver version, CUDA version, VRAM total
- [x] Confirm GPU name: `NVIDIA GeForce RTX 4060 Laptop GPU`
- [x] Run `nvidia-smi --query-gpu=memory.free,memory.total --format=csv` under idle load
- [x] Log result to `nutri-offline/logs/hardware-baseline.txt`
- [x] If driver missing: install via Pop!_OS `nvidia-driver-*` package (do not use random PPA)

---

## 2. Python environment (N-00-02, N-00-03)

- [x] `python3.12 -m venv nutri-offline/venv`
- [x] Activate: `source nutri-offline/venv/bin/activate`
- [x] Install PyTorch with CUDA index matching driver (cu124 wheels)
- [x] Verify: `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"`
- [x] Pin exact versions in `nutri-offline/requirements.txt` + `requirements-lock.txt`

---

## 3. ML stack (N-00-04)

- [x] Install Unsloth per official docs: https://unsloth.ai/docs/get-started/installation
- [x] Install: `peft`, `trl`, `bitsandbytes`, `accelerate`, `datasets`, `huggingface_hub`
- [x] Verify imports: `from unsloth import FastLanguageModel`
- [x] Set `HF_HOME=nutri-offline/models/base` to keep cache local and gitignored

---

## 4. Data / embedding stack (N-00-05)

- [x] Install: `duckdb`, `pandas`, `pyarrow`, `openpyxl` (TACO Excel)
- [x] Install: `sentence-transformers`, `lancedb` (or defer sqlite-vec to Phase 3)
- [x] Verify DuckDB: `duckdb.connect(':memory:').execute('SELECT 42').fetchone()`

---

## 5. Directory layout (N-00-06)

- [x] Create:
  ```
  nutri-offline/
  ├── data/raw/
  ├── data/processed/
  ├── data/datasets/
  ├── models/base/
  ├── models/adapters/
  ├── models/gguf/
  ├── indexes/
  ├── scripts/
  └── logs/
  ```
- [x] Add `nutri-offline/.gitkeep` only if needed — entire `.local/` is gitignored

---

## 6. Smoke train (N-00-07)

- [x] Script: `nutri-offline/scripts/smoke_train.py`
- [x] Load Qwen2.5-3B-Instruct with 4-bit QLoRA via Unsloth
- [x] Run 10 training steps on a tiny inline dataset (3 examples)
- [x] Config: batch_size=1, max_seq_length=512, fp16, paged_adamw_8bit
- [x] Log peak VRAM usage — **2.89 GB** (≤ 7.5 GB)
- [x] If OOM: reduce max_seq_length to 256 and retry (not needed)
- [x] Save smoke adapter to `models/adapters/smoke-test/`

---

## 7. Documentation (N-00-08)

- [x] Create `nutri-offline/ENVIRONMENT.md`:
  - OS, driver, CUDA, Python, all pinned package versions
  - Reproduce steps from clean Pop!_OS install
  - Known RTX 4060 constraints (avoid bf16, batch 1–2)
- [x] Note Hugging Face token requirement (if gated models) — not required for Phase 0 model

---

## Gate

- [x] All P0 tasks complete
- [x] Smoke train green — no OOM, VRAM logged (2.89 GB peak)
- [x] Ready to proceed to [Phase 1 — Data acquisition](../01-data-acquisition/TASKS.md)

**Effort estimate:** 4–8 hours
