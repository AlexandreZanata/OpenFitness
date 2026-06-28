"""Portion intent parser for shorthand nutrition lookups (RAG V2 — RAG-V2-01/02)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class IntentKind(str, Enum):
    LOOKUP = "lookup"
    REASONING = "reasoning"


@dataclass(frozen=True)
class PortionItem:
    food: str
    portion_g: int
    source_hint: str | None = None


@dataclass(frozen=True)
class ParsedIntent:
    kind: IntentKind
    items: list[PortionItem]
    raw: str


REASONING_PATTERN = re.compile(
    r"\b("
    r"quantas?|quantos?|qual|quais|como|por\s*que|porquê|"
    r"saud[aá]vel|compar|melhor|versus|vs\.?|recomend|"
    r"substitu|alerg|cont[eé]m|posso|devo|"
    r"explique|diga|inform"
    r")\b",
    re.IGNORECASE,
)

PORTION_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(g|gramas?|ml|un(?:idade)?s?)\b",
    re.IGNORECASE,
)

SOURCE_HINT_PATTERN = re.compile(r"\b(taco|tbca|fdc|off)\b", re.IGNORECASE)

ITEM_SPLIT_PATTERN = re.compile(r"[,|]")


def _normalize_text(text: str) -> str:
    collapsed = " ".join(text.strip().split())
    return unicodedata.normalize("NFKC", collapsed)


def _parse_portion_g(match: re.Match[str]) -> int:
    amount = float(match.group(1).replace(",", "."))
    unit = match.group(2).lower()
    if unit.startswith("un"):
        return max(1, int(round(amount * 50)))
    return max(1, int(round(amount)))


def _parse_segment(segment: str) -> PortionItem | None:
    text = _normalize_text(segment)
    if not text:
        return None

    source_hint: str | None = None
    source_match = SOURCE_HINT_PATTERN.search(text)
    if source_match:
        source_hint = source_match.group(1).lower()
        text = SOURCE_HINT_PATTERN.sub(" ", text)
        text = _normalize_text(text)

    portion_g = 100
    portion_match = PORTION_PATTERN.search(text)
    if portion_match:
        portion_g = _parse_portion_g(portion_match)
        text = PORTION_PATTERN.sub(" ", text)
        text = _normalize_text(text)

    food = text.strip(" ,-|")
    if not food or len(food) < 2:
        return None

    return PortionItem(food=food, portion_g=portion_g, source_hint=source_hint)


def _looks_like_lookup(text: str, items: list[PortionItem]) -> bool:
    if not items:
        return False
    if "?" in text:
        return False
    if REASONING_PATTERN.search(text):
        return False
    if len(text) > 120:
        return False
    return True


def parse_intent(text: str) -> ParsedIntent:
    """Parse user input into lookup items or reasoning intent."""
    raw = _normalize_text(text)
    if not raw:
        return ParsedIntent(kind=IntentKind.REASONING, items=[], raw=raw)

    segments = [part.strip() for part in ITEM_SPLIT_PATTERN.split(raw) if part.strip()]
    if not segments:
        segments = [raw]

    items: list[PortionItem] = []
    for segment in segments:
        item = _parse_segment(segment)
        if item is not None:
            items.append(item)

    kind = IntentKind.LOOKUP if _looks_like_lookup(raw, items) else IntentKind.REASONING
    return ParsedIntent(kind=kind, items=items, raw=raw)
