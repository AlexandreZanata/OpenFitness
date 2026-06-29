"""Unit tests for household portion resolution (N-09-05, BR-PORT-001)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from household_portions import HouseholdPortionResolver  # noqa: E402
from intent_parser import IntentKind, parse_intent  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "household_portions.jsonl"
HOUSEHOLD_JSON = Path(__file__).resolve().parents[1] / "config" / "semantic" / "household_portions.json"


class HouseholdPortionResolverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolver = HouseholdPortionResolver.from_json(HOUSEHOLD_JSON)

    def test_golden_fixture_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            result = self.resolver.resolve(row["phrase"])
            if row["expected_food"] is None:
                self.assertIsNone(result, row["phrase"])
                continue
            self.assertIsNotNone(result, row["phrase"])
            assert result is not None
            self.assertEqual(result.food, row["expected_food"], row["phrase"])
            self.assertEqual(result.grams, row["expected_grams"], row["phrase"])
            self.assertEqual(result.source, row["expected_source"], row["phrase"])

    def test_apply_to_portion_item(self) -> None:
        item = self.resolver.apply_to_food("uma manga inteira", portion_g=100)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.food, "manga")
        self.assertEqual(item.portion_g, 230)
        self.assertIsNotNone(item.portion_source)


class IntentParserHouseholdTest(unittest.TestCase):
    def test_manga_inteira_nl_query(self) -> None:
        intent = parse_intent("Quantas calorias tem uma manga inteira?")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(len(intent.items), 1)
        self.assertEqual(intent.items[0].food, "manga")
        self.assertEqual(intent.items[0].portion_g, 230)
        self.assertIsNotNone(intent.items[0].portion_source)

    def test_shorthand_manga_inteira(self) -> None:
        intent = parse_intent("manga inteira")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertEqual(intent.items[0].portion_g, 230)
        self.assertEqual(intent.items[0].food, "manga")


if __name__ == "__main__":
    unittest.main()
