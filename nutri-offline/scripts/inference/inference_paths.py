"""Shared paths for NutriOffline inference (Phase 6)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_export_paths = ROOT / "scripts" / "export" / "_paths.py"
_spec = importlib.util.spec_from_file_location("export_paths", _export_paths)
_export = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_export)

GGUF_PATH = _export.GGUF_PATH
INFERENCE_HOST = _export.INFERENCE_HOST
INFERENCE_PORT = _export.INFERENCE_PORT
INFERENCE_URL = _export.INFERENCE_URL
LLAMA_CLI = _export.LLAMA_CLI
LLAMA_CPP_DIR = _export.LLAMA_CPP_DIR
LLAMA_SERVER = _export.LLAMA_SERVER
LOG_DIR = _export.LOG_DIR

RAG_SCRIPTS = ROOT / "scripts" / "rag"
BENCHMARK_LOG = LOG_DIR / "inference-benchmark.json"

SYSTEM_PROMPT_RAG = (
    "Você é um especialista em nutrição. Use APENAS o contexto abaixo para fatos numéricos. "
    "Cite as fontes (TACO, USDA FoodData Central, Open Food Facts)."
)
