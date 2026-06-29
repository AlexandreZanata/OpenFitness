"""Unit tests for RAG V2 portion intent parser (RAG-V2-01, RAG-V2-02)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
sys.path.insert(0, str(APP_DIR))

from intent_parser import (  # noqa: E402
    IntentKind,
    parse_intent,
)


class IntentParserTest(unittest.TestCase):
    def test_single_food_with_mass(self) -> None:
        # GIVEN shorthand food + mass input
        # WHEN parsed
        intent = parse_intent("arroz 100g")
        # THEN one lookup item with 100g portion
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(len(intent.items), 1)
        self.assertEqual(intent.items[0].food, "arroz")
        self.assertEqual(intent.items[0].portion_g, 100)

    def test_multi_item_comma_list(self) -> None:
        # GIVEN comma-separated shorthand items
        intent = parse_intent("arroz 100g, carne 200g")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(len(intent.items), 2)
        self.assertEqual(intent.items[0].food, "arroz")
        self.assertEqual(intent.items[0].portion_g, 100)
        self.assertEqual(intent.items[1].food, "carne")
        self.assertEqual(intent.items[1].portion_g, 200)

    def test_pipe_separator(self) -> None:
        intent = parse_intent("banana | feijão 80g")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(len(intent.items), 2)
        self.assertEqual(intent.items[0].portion_g, 100)
        self.assertEqual(intent.items[1].portion_g, 80)

    def test_implicit_100g_default(self) -> None:
        intent = parse_intent("arroz")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(intent.items[0].portion_g, 100)

    def test_source_hint_extracted(self) -> None:
        intent = parse_intent("arroz cozido taco 100g")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(intent.items[0].source_hint, "taco")
        self.assertNotIn("taco", intent.items[0].food.lower())

    def test_branded_hint_stays_in_food(self) -> None:
        intent = parse_intent("iogurte vigor 170g")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(intent.items[0].portion_g, 170)
        self.assertIn("vigor", intent.items[0].food.lower())

    def test_full_sentence_calories_is_lookup(self) -> None:
        intent = parse_intent("Quantas calorias tem 100g de arroz branco cozido?")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(len(intent.items), 1)
        self.assertEqual(intent.items[0].portion_g, 100)
        self.assertIn("arroz", intent.items[0].food.lower())

    def test_comparison_is_compare(self) -> None:
        intent = parse_intent("Qual tem mais proteína: frango ou ovo?")
        self.assertEqual(intent.kind, IntentKind.COMPARE)
        self.assertIsNotNone(intent.compare)
        assert intent.compare is not None
        self.assertIn("frango", intent.compare.food_a.lower())
        self.assertIn("ovo", intent.compare.food_b.lower())
        self.assertEqual(intent.compare.field, "protein")


if __name__ == "__main__":
    unittest.main()
