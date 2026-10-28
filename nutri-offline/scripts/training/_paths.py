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
DEFAULT_ADAPTER = ADAPTERS_DIR / "nutri-qwen25-3b-v2"
EVAL_PROMPTS = ROOT / "tests" / "fixtures" / "domain_eval_prompts.jsonl"
EVAL_GATE_PROMPTS = ROOT / "tests" / "fixtures" / "domain_eval_gate.jsonl"
EVAL_PROMPTS_V2 = ROOT / "tests" / "fixtures" / "domain_eval_v2_200.jsonl"
EVAL_GATE_V2 = ROOT / "tests" / "fixtures" / "domain_eval_gate_v2.jsonl"
COMPARISON_PROMPTS = ROOT / "tests" / "fixtures" / "domain_eval_comparison.jsonl"

FIXTURE_ALIASES = {
    "v1": EVAL_PROMPTS,
    "v2": EVAL_PROMPTS_V2,
    "gate": EVAL_GATE_PROMPTS,
    "gate-v2": EVAL_GATE_V2,
}
