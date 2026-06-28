"""Unit tests for Phase 4 dataset generation."""

from __future__ import annotations

import unittest

from answers import (
    fmt_g,
    fmt_kcal,
    generate_direct_lookup,
    generate_portion_math,
    source_label,
)


class AnswersTest(unittest.TestCase):
    def test_fmt_kcal_rounds_to_integer(self) -> None:
        self.assertEqual(fmt_kcal(128.26), "128")

    def test_fmt_g_one_decimal(self) -> None:
        self.assertEqual(fmt_g(28.059), "28.1")

    def test_source_label_taco(self) -> None:
        self.assertEqual(source_label("taco"), "TACO (NEPA/UNICAMP)")

    def test_direct_lookup_includes_source_and_macros(self) -> None:
        record = {
            "id": "taco:1",
            "source": "taco",
            "name": "Arroz, tipo 1, cozido",
            "energy_kcal": 128.26,
            "protein_g": 2.52,
            "carbohydrate_g": 28.06,
            "fat_g": 0.23,
            "serving_basis": "100g",
        }
        answer, grounding = generate_direct_lookup(record, "pt")
        self.assertIn("TACO (NEPA/UNICAMP)", answer)
        self.assertIn("128 kcal", answer)
        self.assertIn("28.1g de carboidratos", answer)
        self.assertEqual(grounding["record_ids"], ["taco:1"])

    def test_portion_math_scales_correctly(self) -> None:
        record = {
            "id": "taco:1",
            "source": "taco",
            "name": "Arroz, tipo 1, cozido",
            "energy_kcal": 100.0,
            "protein_g": 10.0,
            "carbohydrate_g": 20.0,
            "fat_g": 5.0,
            "serving_basis": "100g",
        }
        answer, grounding = generate_portion_math(record, 150, "pt")
        self.assertIn("150g", answer)
        self.assertEqual(grounding["values"]["energy_kcal"], 150.0)
        self.assertIn("150 kcal", answer)


if __name__ == "__main__":
    unittest.main()
