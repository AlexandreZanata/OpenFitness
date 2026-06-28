# NutriOffline — Python environment (Phase 0)

> Generated: 2026-06-27 · Machine: Pop!_OS 24.04 · RTX 4060 Laptop 8 GB

## Owner decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python | **3.12** | Available via pyenv; 3.11 not installed |
| Env manager | **venv** | Isolated from system and Android toolchain |
| CUDA toolkit | **System driver only** | Driver 580.159.03; no full toolkit install |
| Project root | `nutri-offline/` | ML workspace at repo root |
| Smoke model | **Qwen2.5-3B-Instruct** (4-bit via Unsloth) | Fits 8 GB VRAM with QLoRA |

## Hardware baseline

| Component | Value |
|-----------|-------|
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| Driver | 580.159.03 |
| CUDA (driver report) | 13.0 |
| VRAM total | 8188 MiB |
| VRAM free (idle) | ~7805 MiB |
| RAM | 31 GiB |
| OS | Pop!_OS 24.04 (Linux) |

Log: `logs/hardware-baseline.txt`

## Pinned stack (verified)

| Package | Version |
|---------|---------|
| Python | 3.12.2 |
| torch | 2.6.0+cu124 |
| transformers | 4.56.1 |
| torchao | 0.13.0 |
| unsloth | 2026.6.9 |
| unsloth_zoo | 2026.6.7 |
| trl | 0.24.0 |
| peft | 0.19.1 |
| bitsandbytes | 0.49.2 |
| duckdb | 1.5.4 |
| lancedb | 0.33.0 |
| sentence-transformers | 5.6.0 |

Full lockfile: `requirements-lock.txt` (from `pip freeze`).

> **Note:** `transformers` 5.x + `torchao` 0.17+ fail on torch 2.6 (`register_constant` missing). Pin `transformers==4.56.1` and `torchao==0.13.0` after Unsloth install.

## Reproduce from clean Pop!_OS

```bash
cd nutri-offline

# 1. GPU check (no Python required)
bash ../../scripts/validate-nutri-hardware.sh

# 2. Virtualenv
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools

# 3. PyTorch (CUDA 12.4 wheels)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 4. Unsloth (cu124 + torch 2.6)
pip install --no-deps git+https://github.com/unslothai/unsloth-zoo.git
pip install "unsloth[cu124-torch260] @ git+https://github.com/unslothai/unsloth.git" --no-build-isolation

# 5. Pin compatible transformers/torchao
pip install 'transformers==4.56.1' 'torchao==0.13.0'

# 6. Data / embedding stack
pip install duckdb pandas pyarrow openpyxl lancedb sentence-transformers

# 7. Validate + smoke train
export HF_HOME="$(pwd)/models/base"
export UNSLOTH_USE_FP16=1
python scripts/validate_environment.py
python scripts/smoke_train.py
```

## RTX 4060 constraints

- Use **fp16** training (`dtype=torch.float16`, `fp16=True`, `bf16=False`)
- Batch size **1–2**; gradient accumulation 4–8
- Peak VRAM on smoke train: **2.89 GB** (10 steps, seq 512, 4-bit QLoRA)
- Set `HF_HOME=models/base` to keep Hugging Face cache local and gitignored

## Hugging Face token

`unsloth/Qwen2.5-3B-Instruct-bnb-4bit` is public — no token required for Phase 0.
Gated models in later phases may need `huggingface-cli login`.

## Phase 0 gate results

| Check | Result |
|-------|--------|
| `nvidia-smi` RTX 4060 ≥ 7.5 GB | PASS (8188 MiB) |
| `torch.cuda.is_available()` | PASS |
| Unsloth import | PASS |
| Smoke train 10 steps, no OOM | PASS (peak 2.89 GB) |
| Directory layout | PASS |
| requirements pinned | PASS |

Adapter artifact: `models/adapters/smoke-test/`

## Phase 6 — llama.cpp (inference)

| Item | Value |
|------|-------|
| Export | Unsloth `save_pretrained_gguf` → q4_k_m |
| GGUF path | `models/gguf/nutri-qwen25-3b-{adapter}-q4_k_m.gguf` |
| llama.cpp | Clone at `llama.cpp/`; **fallback:** symlink Unsloth prebuild from `~/.unsloth/llama.cpp` |
| CUDA build | `cmake -S llama.cpp -B llama.cpp/build -DGGML_CUDA=ON` (requires cmake) |
| Server | `scripts/inference/serve.sh` → `127.0.0.1:8080` |
| Env vars | `NUTRI_ADAPTER`, `NUTRI_GGUF`, `NUTRI_INFERENCE_PORT` |
