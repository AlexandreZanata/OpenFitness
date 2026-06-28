"""Unit tests for RAG V2 source boost reranking (RAG-V2-05, BR-RET-001)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parents[1] / "scripts" / "rag"
sys.path.insert(0, str(RAG_DIR))

from rerank import apply_source_boost, keyword_match_bonus  # noqa: E402
from rag_pipeline import RagHit  # noqa: E402


class SourceBoostTest(unittest.TestCase):
    def test_taco_preferred_when_scores_close(self) -> None:
        # GIVEN TACO and OFF hits with similar raw scores (BR-RET-001)
        off = RagHit(
            score=0.72,
            id="off:1",
            name="Arroz integral",
            source="off",
            rag_context="",
            metadata={},
        )
        taco = RagHit(
            score=0.70,
            id="taco:1",
            name="Arroz, tipo 1, cozido",
            source="taco",
            rag_context="",
            metadata={},
        )
        # WHEN source boost applied
        ranked = apply_source_boost([off, taco])
        # THEN TACO ranks first
        self.assertEqual(ranked[0].source, "taco")

    def test_keyword_bonus_rewards_name_overlap(self) -> None:
        bonus = keyword_match_bonus("arroz branco", "Arroz, tipo 1, cozido")
        self.assertGreater(bonus, 0.0)


if __name__ == "__main__":
    unittest.main()
