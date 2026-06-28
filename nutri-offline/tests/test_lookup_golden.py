"""Golden lookup scenarios for RAG V2 (G1–G4, BR-RET-001/002/003)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
sys.path.insert(0, str(APP_DIR))

from orchestrator import NutriAssistant  # noqa: E402

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
        if len(cells) >= 4 and cells[0] != "**Total**" and cells[0] != "Alimento":
            kcal_cell = cells[3]
            if kcal_cell.isdigit():
                values.append(int(kcal_cell))
    return values


@unittest.skipUnless(
    (Path(__file__).resolve().parents[1] / "indexes" / "nutri-foods").exists(),
    "LanceDB index required for golden lookup tests",
)
class LookupGoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = NutriAssistant()

    def test_g1_arroz_100g_taco_128(self) -> None:
        # GIVEN shorthand arroz lookup
        result = self.assistant.ask("arroz 100g", mode="auto")
        # THEN lookup path with TACO ~128 kcal
        self.assertEqual(result.mode, "lookup")
        self.assertLess(result.latency_ms, 1000)
        self.assertIn("TACO", result.answer)
        kcals = extract_table_kcal(result.answer)
        self.assertTrue(any(within_tolerance(k, 128) for k in kcals))

    def test_g2_banana_100g_taco(self) -> None:
        result = self.assistant.ask("banana 100g", mode="auto")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("TACO", result.answer)
        kcals = extract_table_kcal(result.answer)
        self.assertTrue(any(within_tolerance(k, 98) for k in kcals))

    def test_g3_multi_item_total(self) -> None:
        result = self.assistant.ask("arroz 100g, feijão 100g", mode="auto")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("**Total**", result.answer)
        self.assertIn("205", result.answer)

    def test_g4_unknown_food_no_fabricated_kcal(self) -> None:
        result = self.assistant.ask("nutrixyz 100g", mode="auto")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("Não encontrado", result.answer)
        self.assertEqual(extract_table_kcal(result.answer), [])

    def test_g5_branded_off_product(self) -> None:
        # GIVEN branded shorthand with known OFF product token
        result = self.assistant.ask("iogurte vigor 170g", mode="auto")
        self.assertEqual(result.mode, "lookup")
        self.assertIn("Open Food Facts", result.answer)
        self.assertTrue(any(s["source"] == "off" for s in result.sources))
        self.assertTrue(any("vigor" in s["name"].lower() for s in result.sources))


if __name__ == "__main__":
    unittest.main()
