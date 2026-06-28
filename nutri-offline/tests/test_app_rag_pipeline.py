"""Unit tests for NutriOffline RAG pipeline (Phase 7)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
sys.path.insert(0, str(APP_DIR))

from rag_pipeline import RagPipeline  # noqa: E402


class RagPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = RagPipeline.get(device="cpu")

    def test_arroz_query_returns_results(self) -> None:
        hits = self.pipeline.search("quantas calorias tem arroz branco", top_k=5)
        self.assertGreaterEqual(len(hits), 3)
        self.assertTrue(any("arroz" in h.name.lower() for h in hits))

    def test_build_context_non_empty(self) -> None:
        hits = self.pipeline.search("iogurte grego", top_k=3)
        context = self.pipeline.build_context(hits)
        self.assertIn("kcal", context.lower())


if __name__ == "__main__":
    unittest.main()
