"""Shared paths for NutriOffline RAG index (Phase 3)."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
FOODS_PARQUET = PROCESSED_DIR / "foods.parquet"
FOOD_ALIASES_PARQUET = PROCESSED_DIR / "food_aliases.parquet"
INDEX_DIR = ROOT / "indexes" / "nutri-foods"
INDEX_METADATA = INDEX_DIR / "metadata.json"
LOG_DIR = ROOT / "logs"
CACHE_DIR = ROOT / "indexes" / "cache"

EMBEDDING_MODEL = os.environ.get("NUTRI_EMBED_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = int(os.environ.get("NUTRI_EMBED_DIM", "1024"))
TABLE_NAME = "foods"
SCHEMA_VERSION_V2 = 2

# Candidate models for A/B benchmark (RAG-V2-14)
EMBEDDER_CANDIDATES: dict[str, int] = {
    "BAAI/bge-m3": 1024,
    "BAAI/bge-small-en-v1.5": 384,
    "intfloat/multilingual-e5-small": 384,
}

# v1: TACO + OFF Brazil + FDC Foundation (~108k rows, <4h CPU build)
SCOPE_V1_SQL = """
    source IN ('taco', 'off')
    OR (source = 'fdc' AND json_extract_string(raw_metadata, '$.dataset') = 'foundation')
"""

SCOPE_ALL_SQL = "true"
