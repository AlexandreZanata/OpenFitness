"""Unit tests for Phase 4 dataset generation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "dataset"))

from answers import (
    fmt_g,
    fmt_kcal,
    fmt_nutrient,
    generate_comparison,
    generate_direct_lookup,
    generate_household_portion,
    generate_portion_math,
    generate_unknown_refusal,
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

    def test_unknown_refusal_does_not_invent_macros(self) -> None:
        answer, grounding = generate_unknown_refusal("fruta holográfica", "pt")
        self.assertIn("Não encontrei", answer)
        self.assertIn("TACO", answer)
        self.assertNotIn("kcal", answer)
        self.assertTrue(grounding.get("refusal"))

    def test_household_portion_uses_unit_grams(self) -> None:
        record = {
            "id": "taco:182",
            "source": "taco",
            "name": "Banana, prata",
            "energy_kcal": 98.0,
            "protein_g": 1.3,
            "carbohydrate_g": 26.0,
            "fat_g": 0.1,
            "fiber_g": 2.0,
            "serving_basis": "100g",
        }
        answer, grounding = generate_household_portion(
            record,
            portion_g=86,
            unit_label="uma banana média",
            template_language="pt",
        )
        self.assertIn("86g", answer)
        self.assertIn("84 kcal", answer)
        self.assertEqual(grounding["portion_g"], 86)

    def test_comparison_energy_uses_kcal_not_grams(self) -> None:
        record_a = {
            "id": "taco:3",
            "source": "taco",
            "name": "Arroz cozido",
            "energy_kcal": 128.0,
        }
        record_b = {
            "id": "taco:5",
            "source": "taco",
            "name": "Feijão cozido",
            "energy_kcal": 77.0,
        }
        answer, _ = generate_comparison(record_a, record_b, "energy_kcal", "calorias", "pt")
        self.assertIn("128 kcal", answer)
        self.assertIn("77 kcal", answer)
        self.assertNotIn("128g", answer)


if __name__ == "__main__":
    unittest.main()
