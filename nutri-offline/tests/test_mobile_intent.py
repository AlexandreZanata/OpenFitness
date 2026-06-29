"""Unit tests for mobile NL intent parsing (N-08-21)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from intent_parser import IntentKind, parse_intent  # noqa: E402
from intents_compare import parse_compare  # noqa: E402
from intents_substitute import parse_substitute  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mobile_nl_intents.jsonl"


class MobileIntentFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_fixture_has_at_least_50_utterances(self) -> None:
        self.assertGreaterEqual(len(self.rows), 50)

    def test_golden_fixture_rows(self) -> None:
        for row in self.rows:
            intent = parse_intent(row["utterance"])
            expected = row["expected_kind"]
            if expected == "lookup":
                self.assertEqual(intent.kind, IntentKind.LOOKUP, row["utterance"])
                self.assertGreaterEqual(len(intent.items), 1, row["utterance"])
                if "expected_food" in row:
                    self.assertIn(
                        row["expected_food"].lower(),
                        intent.items[0].food.lower(),
                        row["utterance"],
                    )
                if "expected_portion_g" in row:
                    self.assertEqual(intent.items[0].portion_g, row["expected_portion_g"])
                if row.get("highlight_field"):
                    self.assertEqual(intent.highlight_field, row["highlight_field"])
            elif expected == "compare":
                self.assertEqual(intent.kind, IntentKind.COMPARE, row["utterance"])
                self.assertIsNotNone(intent.compare)
            elif expected == "substitute":
                self.assertEqual(intent.kind, IntentKind.SUBSTITUTE, row["utterance"])
                self.assertIsNotNone(intent.substitute)
            else:
                self.assertEqual(intent.kind, IntentKind.REASONING, row["utterance"])


class CompareSubstitutePatternTest(unittest.TestCase):
    def test_compare_protein_pattern(self) -> None:
        parsed = parse_compare("Qual tem mais proteína: frango ou ovo?")
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.field, "protein")

    def test_substitute_lighter_pattern(self) -> None:
        parsed = parse_substitute("Existe opção mais leve que arroz?")
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.optimize, "kcal")


if __name__ == "__main__":
    unittest.main()
