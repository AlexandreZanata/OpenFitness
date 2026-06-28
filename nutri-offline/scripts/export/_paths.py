"""Shared paths for NutriOffline GGUF export (Phase 6)."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "models"
BASE_MODEL = os.environ.get("NUTRI_BASE_MODEL", "unsloth/Qwen2.5-3B-Instruct-bnb-4bit")
ADAPTER_NAME = os.environ.get("NUTRI_ADAPTER", "smoke-test")
ADAPTER_DIR = MODELS_DIR / "adapters" / ADAPTER_NAME
MERGED_DIR = MODELS_DIR / "merged" / f"nutri-qwen25-3b-{ADAPTER_NAME}"
GGUF_DIR = MODELS_DIR / "gguf"
GGUF_ALT_DIR = MODELS_DIR / "gguf_gguf"
GGUF_QUANT = os.environ.get("NUTRI_GGUF_QUANT", "q4_k_m")
GGUF_FILENAME = f"nutri-qwen25-3b-{ADAPTER_NAME}-{GGUF_QUANT}.gguf"
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
