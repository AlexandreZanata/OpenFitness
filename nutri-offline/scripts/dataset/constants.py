"""Canonical prompts and source labels for Phase 4 dataset generation."""

from __future__ import annotations

SYSTEM_PROMPT = (
    "Você é um assistente especialista em nutrição e composição de alimentos brasileiros. "
    "Sempre cite a fonte dos dados (TACO, USDA FoodData Central, Open Food Facts). "
    "Quando valores exatos forem fornecidos no contexto, use-os com precisão — não invente números. "
    "Se o alimento não estiver nas bases disponíveis, diga claramente que não encontrou — "
    "não invente valores nutricionais."
)

SOURCE_LABELS = {
    "taco": "TACO (NEPA/UNICAMP)",
    "fdc": "USDA FoodData Central",
    "off": "Open Food Facts",
    "tbca": "TBCA",
}

# Target distribution for ~3,000 examples (README strategy table)
STRATEGY_WEIGHTS: dict[str, float] = {
    "direct_lookup": 0.36,
    "comparison": 0.14,
    "portion_math": 0.13,
    "household_portion": 0.04,
    "substitution": 0.09,
    "allergen": 0.09,
    "reasoning": 0.09,
    "unknown_refusal": 0.06,
}

TARGET_TOTAL = 3000
TRAIN_RATIO = 0.90
GROUNDING_TOLERANCE_PCT = 2.0
MIN_TRAIN_EXAMPLES = 2000
MIN_VAL_EXAMPLES = 200
MANUAL_REVIEW_SAMPLE_SIZE = 200
