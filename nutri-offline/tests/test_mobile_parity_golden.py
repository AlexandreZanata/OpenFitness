"""Golden lookup scenarios on mobile pack (G1–G5, N-08-23)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from mobile_paths import VECTORS_DB  # noqa: E402
from mobile_assistant import MobileNutriAssistant  # noqa: E402

TOLERANCE_PCT = 2.0


def within_tolerance(actual: float, expected: float) -> bool:
    if expected == 0:
        return abs(actual) <= 1
    return abs(actual - expected) / abs(expected) * 100 <= TOLERANCE_PCT


def extract_table_kcal(answer: str) -> list[int]:
    rows = [line for line in answer.split("\n") if line.startswith("|") and "kcal" not in line.lower()]
    values: list[int] = []
    for row in rows:
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if len(cells) >= 4 and cells[0] not in {"**Total**", "Alimento"}:
            kcal_cell = cells[3]
            if kcal_cell.replace(".", "").isdigit():
                values.append(int(float(kcal_cell)))
    return values


@unittest.skipUnless(VECTORS_DB.is_file(), "mobile vectors.db required")
class MobileParityGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = MobileNutriAssistant()

    def test_g1_arroz_100g_taco_128(self) -> None:
        result = self.assistant.ask("arroz 100g")
        self.assertEqual(result.mode, "lookup")
        self.assertLess(result.latency_ms, 2000)
        self.assertIn("TACO", result.answer)
        kcals = extract_table_kcal(result.answer)
        self.assertTrue(any(within_tolerance(k, 128) for k in kcals))

    def test_g2_banana_100g_taco(self) -> None:
        result = self.assistant.ask("banana 100g")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("TACO", result.answer)
        kcals = extract_table_kcal(result.answer)
        self.assertTrue(any(within_tolerance(k, 98) for k in kcals))

    def test_g3_multi_item_total(self) -> None:
        result = self.assistant.ask("arroz 100g, feijão 100g")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("**Total**", result.answer)

    def test_g4_unknown_food_no_fabricated_kcal(self) -> None:
        result = self.assistant.ask("nutrixyz 100g")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("Não encontrado", result.answer)
        self.assertEqual(extract_table_kcal(result.answer), [])

    def test_g5_branded_off_product(self) -> None:
        result = self.assistant.ask("iogurte vigor 170g")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("Open Food Facts", result.answer)
        self.assertTrue(any(s["source"] == "off" for s in result.sources))

    def test_nl_calories_routes_to_lookup(self) -> None:
        result = self.assistant.ask("Quantas calorias tem 100g de arroz branco cozido?")
        self.assertEqual(result.mode, "lookup")
        self.assertTrue(
            extract_table_kcal(result.answer)
            or re.search(r"\d+\s*kcal", result.answer.lower())
        )


if __name__ == "__main__":
    unittest.main()
