"""End-to-end mobile assistant — no on-device LLM (N-08-16)."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from intent_parser import IntentKind, parse_intent  # noqa: E402
from lookup_orchestrator import LookupOrchestrator  # noqa: E402
from rag_pipeline import RagHit  # noqa: E402
from response_templates import format_unsupported  # noqa: E402

from mobile_embedder import MobileEmbedder  # noqa: E402
from mobile_search import MobileHit, MobileSearcher  # noqa: E402
from reasoning_engine import CompareEngine, ReasoningResult, SubstituteEngine  # noqa: E402


@dataclass
class MobileNutriResponse:
    answer: str
    sources: list[dict[str, str]]
    model: str
    latency_ms: float
    mode: str
    debug: dict = field(default_factory=dict)


class MobileRagAdapter:
    """Minimal RagPipeline port backed by MobileSearcher."""

    def __init__(self, searcher: MobileSearcher) -> None:
        self._searcher = searcher

    def normalize_lookup_food(self, food: str) -> str:
        normalized, _debug = self._searcher.normalize_food_query(food)
        return normalized

    def search_for_lookup(self, food: str, *, top_k: int = 5, source_hint=None, prefer_branded=False):
        hits = self._searcher.search(
            food,
            top_k=top_k,
            source_hint=source_hint,
            prefer_branded=prefer_branded,
        )
        return [
            RagHit(
                score=hit.score,
                id=hit.id,
                name=hit.name,
                source=hit.source,
                rag_context="",
                metadata=hit.metadata,
            )
            for hit in hits
        ]


class MobileNutriAssistant:
    def __init__(
        self,
        *,
        vectors_db: Path | None = None,
        lexicon_db: Path | None = None,
        embedder: MobileEmbedder | None = None,
    ) -> None:
        from mobile_paths import LEXICON_DB, VECTORS_DB

        kwargs: dict = {}
        if vectors_db:
            kwargs["vectors_db"] = vectors_db
        if lexicon_db:
            kwargs["lexicon_db"] = lexicon_db
        if embedder:
            kwargs["embedder"] = embedder
        self.searcher = MobileSearcher(**kwargs)
        self._lookup = LookupOrchestrator(rag=MobileRagAdapter(self.searcher))  # type: ignore[arg-type]
        self._compare = CompareEngine(self.searcher)
        self._substitute = SubstituteEngine(self.searcher)

    def ask(self, question: str, *, top_k: int = 5, debug: bool = False) -> MobileNutriResponse:
        started = time.perf_counter()
        intent = parse_intent(question)

        if intent.kind == IntentKind.COMPARE and intent.compare is not None:
            result = self._compare.execute(intent.compare)
            return self._to_response(result, started=started, debug=debug)

        if intent.kind == IntentKind.SUBSTITUTE and intent.substitute is not None:
            result = self._substitute.execute(intent.substitute)
            return self._to_response(result, started=started, debug=debug)

        if intent.kind == IntentKind.LOOKUP and intent.items:
            lookup_result = self._lookup.execute(intent, top_k=top_k)
            return MobileNutriResponse(
                answer=lookup_result.answer,
                sources=self._sources_from_hits(lookup_result.hits),
                model="mobile-lookup",
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
                mode="lookup",
                debug={"items": len(intent.items)} if debug else {},
            )

        elapsed = round((time.perf_counter() - started) * 1000, 1)
        return MobileNutriResponse(
            answer=format_unsupported(),
            sources=[],
            model="mobile-rules",
            latency_ms=elapsed,
            mode="clarify",
        )

    def _to_response(
        self,
        result: ReasoningResult,
        *,
        started: float,
        debug: bool,
    ) -> MobileNutriResponse:
        return MobileNutriResponse(
            answer=result.answer,
            sources=self._sources_from_mobile_hits(result.hits),
            model="mobile-rules",
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            mode=result.mode,
            debug={"hits": len(result.hits)} if debug else {},
        )

    @staticmethod
    def _sources_from_hits(hits: list[RagHit]) -> list[dict[str, str]]:
        return [
            {"id": h.id, "name": h.name, "source": h.source, "score": f"{h.score:.3f}"}
            for h in hits
        ]

    @staticmethod
    def _sources_from_mobile_hits(hits: list[MobileHit]) -> list[dict[str, str]]:
        return [
            {"id": h.id, "name": h.name, "source": h.source, "score": f"{h.score:.3f}"}
            for h in hits
        ]
