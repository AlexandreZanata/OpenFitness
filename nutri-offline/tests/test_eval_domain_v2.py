"""Unit tests for domain eval v2 scoring (Phase 11)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parents[1] / "scripts" / "training"
sys.path.insert(0, str(TRAINING_DIR))

from eval_scoring import PASS_THRESHOLDS_V2, aggregate_metrics, score_row  # noqa: E402


class EvalDomainV2Test(unittest.TestCase):
    def test_variant_pass_with_expected_source(self) -> None:
        row = {
            "id": "V1",
            "category": "variant",
            "question": "frango grelhado",
            "expected_record_id": "taco:410",
            "forbidden_record_ids": ["taco:414"],
            "expects_number": 159,
            "number_tolerance_pct": 8,
            "expects_source_citation": True,
        }
        answer = "Segundo a TACO (NEPA/UNICAMP), peito de frango grelhado tem 159 kcal."
        sources = [{"id": "taco:410", "name": "Frango peito", "source": "taco"}]
        scored = score_row(row, answer, sources=sources)
        self.assertEqual(scored.status, "PASS")

    def test_variant_fail_on_forbidden_organ(self) -> None:
        row = {
            "id": "V2",
            "category": "variant",
            "question": "frango",
            "expected_record_id": "taco:410",
            "forbidden_record_ids": ["taco:414"],
        }
        sources = [{"id": "taco:414", "name": "Coração", "source": "taco"}]
        scored = score_row(row, "resposta", sources=sources)
        self.assertEqual(scored.status, "FAIL")

    def test_v2_gate_thresholds(self) -> None:
        from eval_scoring import ScoredRow

        scored = [ScoredRow(f"G{i}", "format", "PASS", "", "q", "a") for i in range(24)]
        scored.append(ScoredRow("G25", "unknown", "PASS", "", "q", "a"))
        metrics = aggregate_metrics(scored, thresholds=PASS_THRESHOLDS_V2)
        self.assertTrue(metrics["pass"])

    def test_v2_fixtures_when_present(self) -> None:
        full = Path(__file__).resolve().parent / "fixtures" / "domain_eval_v2_200.jsonl"
        gate = Path(__file__).resolve().parent / "fixtures" / "domain_eval_gate_v2.jsonl"
        if not full.is_file():
            self.skipTest("run generate_domain_eval_v2.py first")
        full_rows = [json.loads(line) for line in full.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(full_rows), 200)
        gate_rows = [json.loads(line) for line in gate.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(gate_rows), 25)


if __name__ == "__main__":
    unittest.main()
