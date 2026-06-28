"""Shared paths for NutriOffline fine-tuning dataset (Phase 4)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
FOODS_PARQUET = PROCESSED_DIR / "foods.parquet"
DATASETS_DIR = ROOT / "data" / "datasets"
RAW_GENERATED = DATASETS_DIR / "raw_generated.jsonl"
GENERATION_LOG = DATASETS_DIR / "generation_log.jsonl"
TRAIN_JSONL = DATASETS_DIR / "train.jsonl"
VAL_JSONL = DATASETS_DIR / "val.jsonl"
STATS_JSON = DATASETS_DIR / "stats.json"
MANUAL_REVIEW_DIR = DATASETS_DIR / "manual_review"
MANUAL_REVIEW_SAMPLE = MANUAL_REVIEW_DIR / "sample_200.jsonl"
MANUAL_REVIEW_NOTES = MANUAL_REVIEW_DIR / "REVIEW.md"
LOG_DIR = ROOT / "logs"

FDC_FOUNDATION_SQL = """
    source = 'fdc'
    AND json_extract_string(raw_metadata, '$.dataset') = 'foundation'
"""
