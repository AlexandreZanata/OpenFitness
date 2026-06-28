"""Shared paths for NutriOffline RAG index (Phase 3)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
FOODS_PARQUET = PROCESSED_DIR / "foods.parquet"
INDEX_DIR = ROOT / "indexes" / "nutri-foods"
INDEX_METADATA = INDEX_DIR / "metadata.json"
LOG_DIR = ROOT / "logs"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
TABLE_NAME = "foods"

# v1: TACO + OFF Brazil + FDC Foundation (~108k rows, <4h CPU build)
SCOPE_V1_SQL = """
    source IN ('taco', 'off')
    OR (source = 'fdc' AND json_extract_string(raw_metadata, '$.dataset') = 'foundation')
"""

SCOPE_ALL_SQL = "true"
