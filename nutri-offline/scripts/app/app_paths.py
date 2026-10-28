"""Shared paths for NutriOffline app integration (Phase 7)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "logs"
DOCS_DIR = ROOT / "docs"
PID_DIR = ROOT / "run"

APP_HOST = os.environ.get("NUTRI_APP_HOST", "127.0.0.1")
APP_PORT = int(os.environ.get("NUTRI_APP_PORT", "8090"))

DEFAULT_TOP_K = 5
MAX_CONTEXT_TOKENS = 3500  # leave room for question + answer in 4096 window
LLM_MAX_TOKENS = 128  # RAG V2: shorter generation for reasoning fallback
MODEL_NAME = os.environ.get("NUTRI_MODEL_NAME", "nutri-qwen25-3b-v1-q4_k_m")

RAG_DIR = ROOT / "scripts" / "rag"
sys.path.insert(0, str(RAG_DIR))


def resolve_index_scope() -> str:
    """Default index scope: env override, else metadata scope, else v1."""
    env = os.environ.get("NUTRI_INDEX_SCOPE")
    if env in {"v1", "all"}:
        return env
    try:
        from index_catalog import load_index_metadata

        meta = load_index_metadata()
        scope = meta.get("scope")
        if scope in {"v1", "all"}:
            return str(scope)
    except Exception:
        pass
    return "v1"


INDEX_SCOPE = resolve_index_scope()

NO_RAG_HITS_REFUSAL = (
    "Não encontrei esse alimento na base de dados "
    "(TACO, USDA FoodData Central ou Open Food Facts). "
    "Não posso informar valores nutricionais sem uma fonte confiável."
)

SYSTEM_PROMPT = (
    "Você é um assistente especialista em nutrição e composição de alimentos brasileiros. "
    "Use APENAS o contexto abaixo para valores numéricos. "
    "Sempre cite a fonte dos dados (TACO, USDA FoodData Central, Open Food Facts). "
    "Se o alimento não estiver no contexto, diga que não encontrou — não invente números."
)
