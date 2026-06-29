"""Unit tests for mobile QA benchmark scoring (Phase 10, QA-16)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from run_qa_benchmark import score_row, within_tolerance  # noqa: E402


class MobileQaBenchmarkScoringTest(unittest.TestCase):
    def test_within_tolerance_pct(self) -> None:
        self.assertTrue(within_tolerance(128, 130, 5.0))
        self.assertFalse(within_tolerance(128, 140, 5.0))

    def test_lookup_mode_mismatch_fails(self) -> None:
        row = {"id": "T01", "question": "arroz", "expected_mode": "lookup"}
        result = SimpleNamespace(mode="compare", sources=[], answer="")
        scored = score_row(row, result)
        self.assertEqual(scored.status, "FAIL")
        self.assertIn("mode", scored.detail)

    def test_substitute_forbidden_id_fails(self) -> None:
        row = {
            "id": "R07",
            "question": "mais leve que arroz",
            "expected_mode": "substitute",
            "forbidden_substitute_ids": ["taco:29"],
        }
        result = SimpleNamespace(
            mode="substitute",
            sources=[
                {"id": "taco:3", "name": "Arroz"},
                {"id": "taco:29", "name": "Curau"},
            ],
            answer="",
        )
        scored = score_row(row, result)
        self.assertEqual(scored.status, "FAIL")
        self.assertIn("forbidden", scored.detail)

    def test_lookup_record_id_passes(self) -> None:
        row = {
            "id": "R01",
            "question": "100g de arror",
            "expected_mode": "lookup",
            "expected_record_id": "taco:3",
        }
        result = SimpleNamespace(
            mode="lookup",
            sources=[{"id": "taco:3", "name": "Arroz, tipo 1, cozido", "source": "taco"}],
            answer="| Arroz | 100g |",
        )
        scored = score_row(row, result)
        self.assertEqual(scored.status, "PASS")


if __name__ == "__main__":
    unittest.main()
