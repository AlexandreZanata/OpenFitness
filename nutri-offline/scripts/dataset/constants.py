"""Canonical prompts and source labels for Phase 4 dataset generation."""

from __future__ import annotations

SYSTEM_PROMPT = (
    "Você é um assistente especialista em nutrição e composição de alimentos brasileiros. "
    "Sempre cite a fonte dos dados (TACO, USDA FoodData Central, Open Food Facts). "
    "Quando valores exatos forem fornecidos no contexto, use-os com precisão — não invente números."
)

SOURCE_LABELS = {
    "taco": "TACO (NEPA/UNICAMP)",
    "fdc": "USDA FoodData Central",
    "off": "Open Food Facts",
    "tbca": "TBCA",
}

# Target distribution for ~3,000 examples (README strategy table)
STRATEGY_WEIGHTS: dict[str, float] = {
    "direct_lookup": 0.40,
    "comparison": 0.15,
    "portion_math": 0.15,
    "substitution": 0.10,
    "allergen": 0.10,
    "reasoning": 0.10,
}

TARGET_TOTAL = 3000
TRAIN_RATIO = 0.90
GROUNDING_TOLERANCE_PCT = 2.0
MIN_TRAIN_EXAMPLES = 2000
MIN_VAL_EXAMPLES = 200
MANUAL_REVIEW_SAMPLE_SIZE = 200
