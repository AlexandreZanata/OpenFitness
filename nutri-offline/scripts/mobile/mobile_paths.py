"""Shared paths for NutriOffline mobile pack (Phase 8)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
FOODS_PARQUET = PROCESSED_DIR / "foods.parquet"
FOOD_ALIASES_PARQUET = PROCESSED_DIR / "food_aliases.parquet"
MOBILE_RECORD_IDS_PARQUET = PROCESSED_DIR / "mobile_record_ids.parquet"

FOOD_ONTOLOGY_JSON = ROOT / "config" / "semantic" / "food_ontology.json"
HOUSEHOLD_PORTIONS_JSON = ROOT / "config" / "semantic" / "household_portions.json"
MOBILE_INDEX_DIR = ROOT / "indexes" / "nutri-mobile"
VECTORS_DB = MOBILE_INDEX_DIR / "vectors.db"
LEXICON_DB = MOBILE_INDEX_DIR / "lexicon.db"
SYNONYMS_DB = MOBILE_INDEX_DIR / "synonyms.db"
EMBEDDER_ONNX = MOBILE_INDEX_DIR / "embedder.onnx"
PACK_MANIFEST = MOBILE_INDEX_DIR / "pack.manifest.json"
PACK_ARTIFACT = MOBILE_INDEX_DIR / "nutri-mobile.pack"

LOG_DIR = ROOT / "logs"
SPIKE_REPORT = LOG_DIR / "mobile-sqlite-vec-spike.json"

MOBILE_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
MOBILE_EMBED_DIM = 384
DEFAULT_OFF_TIER_C_SIZE = 8000
