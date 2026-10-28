"""Shared paths for NutriOffline GGUF export (Phase 6)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_export_dir = Path(__file__).resolve().parent
_gguf_spec = importlib.util.spec_from_file_location(
    "gguf_paths", _export_dir / "gguf_paths.py"
)
_gguf = importlib.util.module_from_spec(_gguf_spec)
assert _gguf_spec.loader is not None
_gguf_spec.loader.exec_module(_gguf)
gguf_filename = _gguf.gguf_filename
gguf_model_stem = _gguf.gguf_model_stem

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
BASE_MODEL = os.environ.get("NUTRI_BASE_MODEL", "unsloth/Qwen2.5-3B-Instruct-bnb-4bit")
ADAPTER_NAME = os.environ.get("NUTRI_ADAPTER", "nutri-qwen25-3b-v1")
ADAPTER_DIR = MODELS_DIR / "adapters" / ADAPTER_NAME
MERGED_DIR = MODELS_DIR / "merged" / gguf_model_stem(ADAPTER_NAME)
GGUF_DIR = MODELS_DIR / "gguf"
GGUF_ALT_DIR = MODELS_DIR / "gguf_gguf"
GGUF_QUANT = os.environ.get("NUTRI_GGUF_QUANT", "q4_k_m")
GGUF_FILENAME = gguf_filename(ADAPTER_NAME, quant=GGUF_QUANT)
GGUF_PATH = GGUF_DIR / GGUF_FILENAME
LOG_DIR = ROOT / "logs"
LLAMA_CPP_DIR = ROOT / "llama.cpp"
LLAMA_SERVER = LLAMA_CPP_DIR / "build" / "bin" / "llama-server"
LLAMA_CLI = LLAMA_CPP_DIR / "build" / "bin" / "llama-cli"
MODELFILE_PATH = GGUF_DIR / "Modelfile"

INFERENCE_HOST = os.environ.get("NUTRI_INFERENCE_HOST", "127.0.0.1")
INFERENCE_PORT = int(os.environ.get("NUTRI_INFERENCE_PORT", "8080"))
INFERENCE_URL = f"http://{INFERENCE_HOST}:{INFERENCE_PORT}/v1/chat/completions"

MAX_SEQ_LENGTH = 2048
