"""Unit tests for mobile compare/substitute engines (N-08-22)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
sys.path.insert(0, str(MOBILE_DIR))
sys.path.insert(0, str(APP_DIR))

from intents_compare import CompareIntent  # noqa: E402
from intents_substitute import SubstituteIntent  # noqa: E402
from mobile_search import MobileHit  # noqa: E402
from reasoning_engine import CompareEngine, SubstituteEngine  # noqa: E402


def _hit(
    *,
    record_id: str,
    name: str,
    source: str = "taco",
    protein: float = 10.0,
    kcal: float = 100.0,
    carb: float = 20.0,
    category: str = "Cereals",
) -> MobileHit:
    return MobileHit(
        score=0.9,
        id=record_id,
        name=name,
        source=source,
        metadata={
            "energy_kcal": kcal,
            "protein_g": protein,
            "carbohydrate_g": carb,
            "fat_g": 1.0,
            "fiber_g": 2.0,
            "serving_basis": "100g",
            "category": category,
            "brand": "",
        },
    )


class CompareEngineTest(unittest.TestCase):
    def test_compare_protein_winner(self) -> None:
        searcher = MagicMock()
        searcher.search.side_effect = [
            [_hit(record_id="taco:1", name="Frango", protein=27.0)],
            [_hit(record_id="taco:2", name="Ovo", protein=13.0)],
        ]
        engine = CompareEngine(searcher)
        result = engine.execute(
            CompareIntent(food_a="frango", food_b="ovo", field="protein")
        )
        self.assertEqual(result.mode, "compare")
        self.assertIn("Frango", result.answer)
        self.assertIn("proteína", result.answer.lower())


class SubstituteEngineTest(unittest.TestCase):
    def test_substitute_finds_lower_carb_staple(self) -> None:
        original = _hit(record_id="taco:3", name="Arroz branco", carb=28.0, category="Cereais")
        alternative = _hit(record_id="taco:91", name="Batata, inglesa, cozida", carb=11.9, category="Verduras")
        searcher = MagicMock()
        searcher.search.return_value = [original]
        searcher.search_staple_candidates.return_value = [alternative, original]
        engine = SubstituteEngine(searcher)
        result = engine.execute(
            SubstituteIntent(food="arroz", optimize="carb")
        )
        self.assertEqual(result.mode, "substitute")
        self.assertIn("Batata", result.answer)


if __name__ == "__main__":
    unittest.main()
