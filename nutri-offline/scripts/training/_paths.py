"""Shared paths for NutriOffline QLoRA training (Phase 5)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRAINING_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = TRAINING_DIR / "config.yaml"
LOG_DIR = ROOT / "logs"
ADAPTERS_DIR = ROOT / "models" / "adapters"
DATASETS_DIR = ROOT / "data" / "datasets"
TRAIN_JSONL = DATASETS_DIR / "train.jsonl"
VAL_JSONL = DATASETS_DIR / "val.jsonl"
STATS_JSON = DATASETS_DIR / "stats.json"
HF_HOME = ROOT / "models" / "base"
