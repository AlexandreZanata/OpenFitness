"""Unit tests for regex intent gate (N-09-08, BR-INT-001)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from intent_regex_gate import (  # noqa: E402
    BR_INT_001_MIN_ACCURACY,
    evaluate_intent_regex_fixture,
    load_intent_fixture,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mobile_nl_intents.jsonl"


class IntentRegexGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_intent_fixture(FIXTURE)

    def test_fixture_has_at_least_50_utterances(self) -> None:
        self.assertGreaterEqual(len(self.rows), 50)

    def test_regex_accuracy_meets_br_int_001_threshold(self) -> None:
        report = evaluate_intent_regex_fixture(self.rows)
        self.assertGreaterEqual(report["accuracy"], BR_INT_001_MIN_ACCURACY)
        self.assertFalse(report["intent_embedder_required"])
        self.assertEqual(report["failures"], [])


if __name__ == "__main__":
    unittest.main()
