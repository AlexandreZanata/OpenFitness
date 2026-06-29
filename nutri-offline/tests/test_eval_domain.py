"""Unit tests for Phase 5 domain evaluation scoring."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "training"))

from eval_scoring import (  # noqa: E402
    aggregate_metrics,
    acknowledges_unknown,
    has_definitive_nutrition_claim,
    load_eval_prompts,
    score_row,
)
from training_metrics import check_loss_stable  # noqa: E402


class EvalScoringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ROOT / "tests" / "fixtures" / "domain_eval_prompts.jsonl"

    def test_fixture_has_fifty_prompts(self) -> None:
        rows = load_eval_prompts(self.fixture)
        self.assertEqual(len(rows), 50)
        categories = {row["category"] for row in rows}
        self.assertIn("unknown", categories)
        self.assertIn("rag", categories)

    def test_format_pass_with_source_and_number(self) -> None:
        row = {
            "id": "T01",
            "category": "format",
            "question": "arroz",
            "expects_source_citation": True,
            "expects_number": 128,
            "number_tolerance_pct": 5,
        }
        answer = "Segundo a TACO (NEPA/UNICAMP), 100g de arroz cozido tem cerca de 128 kcal."
        scored = score_row(row, answer)
        self.assertEqual(scored.status, "PASS")

    def test_format_fail_without_source(self) -> None:
        row = {"id": "T02", "category": "format", "question": "arroz", "expects_source_citation": True}
        scored = score_row(row, "Arroz tem 128 kcal por 100g.")
        self.assertEqual(scored.status, "FAIL")
        self.assertIn("source", scored.detail)

    def test_unknown_pass_when_acknowledged(self) -> None:
        row = {"id": "T03", "category": "unknown", "question": "fruta rara"}
        answer = "Não tenho dados na base para esse alimento fictício."
        self.assertTrue(acknowledges_unknown(answer))
        scored = score_row(row, answer)
        self.assertEqual(scored.status, "PASS")

    def test_unknown_fail_on_definitive_claim(self) -> None:
        row = {"id": "T04", "category": "unknown", "question": "fruta rara"}
        answer = "A fruta rara tem 250 kcal e 12g de proteína por 100g."
        self.assertTrue(has_definitive_nutrition_claim(answer))
        scored = score_row(row, answer)
        self.assertEqual(scored.status, "FAIL")

    def test_rag_pass_when_number_matches_context(self) -> None:
        row = {
            "id": "T05",
            "category": "rag",
            "question": "calorias?",
            "expects_number": 128,
            "number_tolerance_pct": 2,
        }
        scored = score_row(row, "Conforme o contexto, são 128 kcal.")
        self.assertEqual(scored.status, "PASS")

    def test_aggregate_metrics_gate_pass(self) -> None:
        from eval_scoring import ScoredRow

        scored = [
            ScoredRow("1", "format", "PASS", "", "q", "a"),
            ScoredRow("2", "format", "PASS", "", "q", "a"),
            ScoredRow("3", "unknown", "PASS", "", "q", "a"),
            ScoredRow("4", "rag", "PASS", "", "q", "a"),
        ]
        metrics = aggregate_metrics(scored)
        self.assertTrue(metrics["pass"])


class TrainingMetricsTest(unittest.TestCase):
    def test_stable_loss_history_passes(self) -> None:
        history = [
            {"loss": 1.0, "step": 1},
            {"loss": 0.8, "step": 2},
            {"loss": 0.6, "step": 3},
            {"loss": 0.4, "step": 4},
            {"loss": 0.3, "step": 5},
            {"loss": 0.25, "step": 6},
            {"loss": 0.22, "step": 7},
            {"loss": 0.2, "step": 8},
            {"loss": 0.19, "step": 9},
            {"loss": 0.18, "step": 10},
        ]
        history.append({"eval_loss": 0.25, "step": 10})
        result = check_loss_stable(history)
        self.assertTrue(result["pass"])

    def test_divergent_loss_fails(self) -> None:
        history = [
            {"loss": 0.2, "step": i} for i in range(1, 10)
        ] + [{"loss": 0.5, "step": 10}, {"loss": 0.6, "step": 11}, {"loss": 0.7, "step": 12}]
        result = check_loss_stable(history)
        self.assertFalse(result["pass"])


if __name__ == "__main__":
    unittest.main()
