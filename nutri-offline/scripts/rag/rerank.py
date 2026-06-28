"""Source boost and keyword scoring for RAG retrieval (RAG-V2-05, BR-RET-001)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import replace
from typing import Protocol


SOURCE_BOOST: dict[str, float] = {
    "taco": 0.15,
    "tbca": 0.12,
    "fdc": 0.05,
    "off": 0.0,
}


class ScoredHit(Protocol):
    score: float
    source: str


def normalize_tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return [token for token in re.split(r"[^a-z0-9]+", stripped) if len(token) >= 2]


def keyword_match_bonus(query: str, name: str) -> float:
    """Small score bonus when query tokens appear in the candidate name."""
    query_tokens = set(normalize_tokens(query))
    name_tokens = set(normalize_tokens(name))
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & name_tokens)
    return min(0.12, overlap * 0.04)


def preparation_bonus(name: str) -> float:
    """Prefer cooked/generic table entries over raw ingredients for portions."""
    lowered = name.lower()
    bonus = 0.0
    if "cozido" in lowered or "grelhad" in lowered or "crua" in lowered:
        bonus += 0.06
    if " cru" in lowered or lowered.endswith("cru"):
        bonus -= 0.08
    return bonus


def apply_source_boost(hits: list[ScoredHit]) -> list[ScoredHit]:
    """Rerank hits with source authority boost (BR-RET-001)."""
    boosted = [
        replace(hit, score=hit.score + SOURCE_BOOST.get(hit.source.lower(), 0.0))  # type: ignore[type-var]
        for hit in hits
    ]
    boosted.sort(key=lambda item: item.score, reverse=True)
    return boosted
