"""Unit tests for G-RET retrieval benchmark (Phase 11)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

RAG_DIR = Path(__file__).resolve().parents[1] / "scripts" / "rag"
sys.path.insert(0, str(RAG_DIR))

from benchmark_retrieval import (  # noqa: E402
    bucket_metrics,
    evaluate_query,
    gate_pass,
)
from rag_pipeline import RagHit  # noqa: E402


class RetrievalBenchmarkTest(unittest.TestCase):
    def test_negative_bucket_passes_without_hits(self) -> None:
        rag = MagicMock()
        rag.search_for_lookup.return_value = []
        result = evaluate_query(rag, {"id": "N1", "bucket": "negative", "query": "xyz"})
        self.assertTrue(result.passed)

    def test_taco_recall_at_1(self) -> None:
        rag = MagicMock()
        rag.search_for_lookup.return_value = [
            RagHit(0.9, "taco:1", "Arroz", "taco", "", {}),
        ]
        row = {"id": "T1", "bucket": "taco", "query": "arroz", "expected_id": "taco:1"}
        result = evaluate_query(rag, row)
        self.assertTrue(result.passed)

    def test_gate_pass_requires_core_buckets(self) -> None:
        metrics = {
            "taco": {"pass": True},
            "off": {"pass": True},
            "generic_pt": {"pass": True},
            "negative": {"pass": True},
            "fdc_branded": {"pass": True},
        }
        self.assertTrue(gate_pass(metrics, index_scope="all"))

    def test_gate_fixture_exists(self) -> None:
        path = Path(__file__).resolve().parent / "fixtures" / "retrieval_gate_sample.jsonl"
        if not path.is_file():
            self.skipTest("run generate_retrieval_corpus.py first")
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 100)
        first = json.loads(lines[0])
        self.assertIn("bucket", first)
        self.assertIn("query", first)


if __name__ == "__main__":
    unittest.main()
