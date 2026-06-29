"""Desktop LanceDB adapter for compare/substitute rule engines (admin ↔ mobile parity)."""

from __future__ import annotations

import sys
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
MOBILE_DIR = Path(__file__).resolve().parents[1] / "mobile"
sys.path.insert(0, str(RAG_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from hybrid_search import HybridHit, KeywordSearcher  # noqa: E402
from rag_pipeline import RagHit, RagPipeline  # noqa: E402
from reasoning_engine import ReasoningHit  # noqa: E402


def _hybrid_to_reasoning(hit: HybridHit) -> ReasoningHit:
    return ReasoningHit(
        score=hit.score,
        id=hit.id,
        name=hit.name,
        source=hit.source,
        metadata=hit.metadata,
    )


def _rag_to_reasoning(hit: RagHit) -> ReasoningHit:
    return ReasoningHit(
        score=hit.score,
        id=hit.id,
        name=hit.name,
        source=hit.source,
        metadata=hit.metadata,
    )


class RagReasoningSearcher:
    """MobileSearcher-compatible port backed by LanceDB + foods.parquet."""

    def __init__(self, rag: RagPipeline | None = None) -> None:
        self._rag = rag or RagPipeline.get()
        self._keyword = KeywordSearcher()

    def search(
        self,
        food: str,
        *,
        top_k: int = 5,
        source_hint: str | None = None,
        prefer_branded: bool = False,
    ) -> list[ReasoningHit]:
        hits = self._rag.search_for_lookup(
            food,
            top_k=top_k,
            source_hint=source_hint,
            prefer_branded=prefer_branded,
        )
        return [_rag_to_reasoning(hit) for hit in hits]

    def search_staple_candidates(
        self,
        *,
        exclude_id: str | None = None,
    ) -> list[ReasoningHit]:
        return [
            _hybrid_to_reasoning(hit)
            for hit in self._keyword.search_staple_candidates(exclude_id=exclude_id)
        ]

    def search_category(
        self,
        category: str,
        *,
        exclude_id: str | None = None,
        top_k: int = 30,
    ) -> list[ReasoningHit]:
        return [
            _hybrid_to_reasoning(hit)
            for hit in self._keyword.search_category(
                category,
                exclude_id=exclude_id,
                top_k=top_k,
            )
        ]
