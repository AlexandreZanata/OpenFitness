"""Deterministic lookup path — no LLM for shorthand queries (RAG V2 — RAG-V2-10/11)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
sys.path.insert(0, str(RAG_DIR))

from intent_parser import IntentKind, ParsedIntent, PortionItem, parse_intent
from rag_pipeline import RagHit, RagPipeline
from rerank import apply_source_boost, normalize_tokens  # noqa: E402
from response_formatter import format_lookup_table

MIN_LOOKUP_SCORE = 0.08
TACO_OFF_SCORE_GAP = 0.05

BRAND_HINTS = frozenset(
    {
        "vigor",
        "nestle",
        "danone",
        "itambé",
        "itambe",
        "qualita",
        "tio joão",
        "tio joao",
        "camil",
        "batavo",
        "piracanjuba",
    }
)


def _prefer_branded(item: PortionItem) -> bool:
    lowered = item.food.lower()
    return any(brand in lowered for brand in BRAND_HINTS)


@dataclass
class LookupResult:
    answer: str
    hits: list[RagHit]
    items: list[PortionItem]
    all_matched: bool


def _has_name_overlap(food: str, name: str) -> bool:
    food_tokens = set(normalize_tokens(food))
    name_tokens = set(normalize_tokens(name))
    return bool(food_tokens & name_tokens)


def _select_best_hit(
    hits: list[RagHit],
    *,
    food: str,
    source_hint: str | None,
    min_score: float,
    require_overlap: bool,
) -> RagHit | None:
    if not hits:
        return None

    boosted = apply_source_boost(hits)
    if source_hint:
        hinted = [h for h in boosted if h.source.lower() == source_hint.lower()]
        if hinted:
            boosted = hinted + [h for h in boosted if h not in hinted]

    best = boosted[0]
    if best.score < min_score:
        return None
    if require_overlap and not _has_name_overlap(food, best.name):
        return None

    taco_candidates = [h for h in boosted if h.source.lower() == "taco"]
    off_candidates = [h for h in boosted if h.source.lower() == "off"]
    if taco_candidates and off_candidates:
        top_off = off_candidates[0]
        best_taco = taco_candidates[0]
        if top_off.score - best_taco.score <= TACO_OFF_SCORE_GAP:
            return best_taco

    return best


def retrieve_item(
    pipeline: RagPipeline,
    item: PortionItem,
    *,
    top_k: int = 5,
    min_score: float = MIN_LOOKUP_SCORE,
) -> RagHit | None:
    """Retrieve the best food record for a single parsed item (BR-RET-003)."""
    hits = pipeline.search_for_lookup(
        item.food,
        top_k=top_k,
        source_hint=item.source_hint,
        prefer_branded=_prefer_branded(item),
    )
    return _select_best_hit(
        hits,
        food=item.food,
        source_hint=item.source_hint,
        min_score=min_score,
        require_overlap=not _prefer_branded(item),
    )


class LookupOrchestrator:
    """Grounded lookup path that bypasses the LLM for shorthand queries."""

    def __init__(
        self,
        *,
        rag: RagPipeline | None = None,
        min_score: float = MIN_LOOKUP_SCORE,
    ) -> None:
        self.rag = rag or RagPipeline.get()
        self.min_score = min_score

    def can_handle(self, intent: ParsedIntent) -> bool:
        return intent.kind == IntentKind.LOOKUP and bool(intent.items)

    def execute(self, intent: ParsedIntent, *, top_k: int = 5) -> LookupResult:
        rows: list[tuple[PortionItem, RagHit | None]] = []
        hits: list[RagHit] = []

        for item in intent.items:
            hit = retrieve_item(self.rag, item, top_k=top_k, min_score=self.min_score)
            rows.append((item, hit))
            if hit is not None:
                hits.append(hit)

        all_matched = all(hit is not None for _, hit in rows)
        answer = format_lookup_table(rows)
        return LookupResult(answer=answer, hits=hits, items=intent.items, all_matched=all_matched)


def try_lookup(
    question: str,
    *,
    rag: RagPipeline | None = None,
    top_k: int = 5,
    min_score: float = MIN_LOOKUP_SCORE,
) -> LookupResult | None:
    """Parse and run lookup path when input is shorthand portion syntax."""
    intent = parse_intent(question)
    orchestrator = LookupOrchestrator(rag=rag, min_score=min_score)
    if not orchestrator.can_handle(intent):
        return None
    return orchestrator.execute(intent, top_k=top_k)
