"""Unit tests for FoodRecord schema (Phase 2)."""

from __future__ import annotations

import unittest

from schema import FoodRecord, normalize_name


class FoodRecordSchemaTest(unittest.TestCase):
    def test_normalize_name_strips_accents_and_lowercases(self) -> None:
        self.assertEqual(normalize_name("Arroz, Branco, Cozido"), "arroz, branco, cozido")
        self.assertEqual(normalize_name("  Açúcar  "), "acucar")

    def test_food_record_rejects_negative_energy(self) -> None:
        with self.assertRaises(ValueError):
            FoodRecord.build(
                source="taco",
                native_id="1",
                name="Test food",
                language="pt-BR",
                source_url="https://example.com",
                energy_kcal=-1.0,
            )

    def test_make_id_format(self) -> None:
        record = FoodRecord.build(
            source="fdc",
            native_id="12345",
            name="Apple, raw",
            language="en",
            source_url="https://fdc.nal.usda.gov/",
        )
        self.assertEqual(record.id, "fdc:12345")
        self.assertEqual(record.name_normalized, "apple, raw")


if __name__ == "__main__":
    unittest.main()
