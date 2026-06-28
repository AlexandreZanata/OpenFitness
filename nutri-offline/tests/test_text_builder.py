"""Unit tests for RAG text builder (Phase 3)."""

from __future__ import annotations

import unittest

from text_builder import build_embedding_text, build_rag_context


class TextBuilderTest(unittest.TestCase):
    def test_taco_arroz_embedding_text_shape(self) -> None:
        record = {
            "name": "Arroz, tipo 1, cozido",
            "category": "Cereais e derivados",
            "source": "taco",
            "serving_basis": "100g",
            "energy_kcal": 128.26,
            "protein_g": 2.52,
            "carbohydrate_g": 28.06,
            "fat_g": 0.23,
            "ingredients_text": None,
        }
        text = build_embedding_text(record)
        self.assertIn("Arroz, tipo 1, cozido", text)
        self.assertIn("Source: taco", text)
        self.assertIn("128.26 kcal", text)
        self.assertIn("28.06g", text)
        self.assertNotIn("None", text)

    def test_rag_context_format(self) -> None:
        record = {
            "source": "taco",
            "name": "Banana, prata, crua",
            "serving_basis": "100g",
            "energy_kcal": 98.25,
            "protein_g": 1.09,
            "carbohydrate_g": 26.0,
            "fat_g": 0.12,
        }
        context = build_rag_context(record)
        self.assertEqual(
            context,
            "[taco] Banana, prata, crua (100g): 98.25 kcal, P 1.09g, C 26g, G 0.12g",
        )

    def test_ingredients_truncated(self) -> None:
        record = {
            "name": "Produto teste",
            "source": "off",
            "serving_basis": "100g",
            "ingredients_text": "x" * 600,
        }
        text = build_embedding_text(record)
        self.assertIn("...", text)
        self.assertLessEqual(len(text.split("Ingredients: ")[1]), 503)


if __name__ == "__main__":
    unittest.main()
