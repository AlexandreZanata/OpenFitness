"""Portion intent parser for shorthand nutrition lookups (RAG V2 — RAG-V2-01/02)."""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from intents_compare import CompareIntent
    from intents_substitute import SubstituteIntent


class IntentKind(str, Enum):
    LOOKUP = "lookup"
    COMPARE = "compare"
    SUBSTITUTE = "substitute"
    REASONING = "reasoning"


@dataclass(frozen=True)
class PortionItem:
    food: str
    portion_g: int
    source_hint: str | None = None
    portion_source: str | None = None


@dataclass(frozen=True)
class ParsedIntent:
    kind: IntentKind
    items: list[PortionItem]
    raw: str
    compare: CompareIntent | None = None
    substitute: SubstituteIntent | None = None
    highlight_field: str | None = None


REASONING_PATTERN = re.compile(
    r"\b("
    r"quantas?|quantos?|qual|quais|como|por\s*que|porquê|"
    r"saud[aá]vel|compar|melhor|versus|vs\.?|recomend|"
    r"substitu|alerg|cont[eé]m|posso|devo|"
    r"explique|diga|inform"
    r")\b",
    re.IGNORECASE,
)

COACHING_PATTERN = re.compile(
    r"\b(me ajude|emagrecer|diet[ao]|plano alimentar|coaching)\b",
    re.IGNORECASE,
)

PORTION_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(g|gramas?|ml|un(?:idade)?s?)\b",
    re.IGNORECASE,
)

SOURCE_HINT_PATTERN = re.compile(r"\b(taco|tbca|fdc|off)\b", re.IGNORECASE)

ITEM_SPLIT_PATTERN = re.compile(r"[,|]")

NL_CALORIES_PATTERN = re.compile(
    r"quantas?\s+calorias\s+(?:tem\s+)?(?:(?P<portion>\d+(?:[.,]\d+)?)\s*(?:g|gramas?)\s+(?:de\s+)?)?(?P<food>.+?)\??$",
    re.IGNORECASE,
)
NL_CALORIES_ALT_PATTERN = re.compile(
    r"calorias\s+(?:de\s+)?(?P<food>.+?)\s+(?P<portion>\d+(?:[.,]\d+)?)\s*(?:g|gramas?)\??$",
    re.IGNORECASE,
)
NL_MACRO_PATTERN = re.compile(
    r"quanto\s+de\s+(?P<macro>prote[ií]na|fibra|carboidratos?|gordura)\s+(?:tem\s+)?"
    r"(?:(?P<portion1>\d+(?:[.,]\d+)?)\s*(?:g|gramas?)\s+(?:de\s+)?)?(?P<food1>.+?)\??$",
    re.IGNORECASE,
)
NL_MACRO_ALT_PATTERN = re.compile(
    r"quanto\s+de\s+(?P<macro>prote[ií]na|fibra|carboidratos?|gordura)\s+(?:tem\s+)?"
    r"(?P<food2>.+?)\s+(?P<portion2>\d+(?:[.,]\d+)?)\s*(?:g|gramas?)\??$",
    re.IGNORECASE,
)

MACRO_FIELD_MAP = {
    "proteina": "protein",
    "proteína": "protein",
    "fibra": "fiber",
    "carboidrato": "carb",
    "carboidratos": "carb",
    "gordura": "fat",
}


def _mobile_intent_modules():
    mobile_dir = Path(__file__).resolve().parents[1] / "mobile"
    if str(mobile_dir) not in sys.path:
        sys.path.insert(0, str(mobile_dir))
    from intents_compare import parse_compare  # noqa: E402
    from intents_substitute import parse_substitute  # noqa: E402

    return parse_compare, parse_substitute


def _household_portion_resolver():
    mobile_dir = Path(__file__).resolve().parents[1] / "mobile"
    if str(mobile_dir) not in sys.path:
        sys.path.insert(0, str(mobile_dir))
    from household_portions import HouseholdPortionResolver  # noqa: E402

    return HouseholdPortionResolver.from_json()


def _apply_household_portions(
    items: list[PortionItem],
    *,
    source_phrases: list[str] | None = None,
    resolve_phrases: list[str] | None = None,
) -> list[PortionItem]:
    if not items:
        return items
    resolver = _household_portion_resolver()
    resolved_items: list[PortionItem] = []
    for index, item in enumerate(items):
        source_phrase = item.food
        resolve_phrase = item.food
        if source_phrases is not None and index < len(source_phrases):
            source_phrase = source_phrases[index]
        if resolve_phrases is not None and index < len(resolve_phrases):
            resolve_phrase = resolve_phrases[index]
        if PORTION_PATTERN.search(source_phrase):
            resolved_items.append(item)
            continue
        match = resolver.resolve(resolve_phrase)
        if match is None:
            resolved_items.append(item)
            continue
        resolved_items.append(
            PortionItem(
                food=match.food,
                portion_g=match.grams,
                source_hint=item.source_hint,
                portion_source=match.source,
            )
        )
    return resolved_items


def _parse_nl_lookup(raw: str) -> tuple[list[PortionItem], str | None]:
    match = NL_CALORIES_PATTERN.search(raw)
    if match:
        food = match.group("food").strip(" ?.:,")
        portion_raw = match.group("portion")
        portion_g = 100
        if portion_raw:
            portion_g = max(1, int(round(float(portion_raw.replace(",", ".")))))
        return [PortionItem(food=food, portion_g=portion_g)], None

    alt = NL_CALORIES_ALT_PATTERN.search(raw)
    if alt:
        food = alt.group("food").strip(" ?.:,")
        portion_g = max(1, int(round(float(alt.group("portion").replace(",", ".")))))
        return [PortionItem(food=food, portion_g=portion_g)], None

    macro_alt = NL_MACRO_ALT_PATTERN.search(raw)
    if macro_alt:
        food = macro_alt.group("food2").strip(" ?.:,")
        macro = macro_alt.group("macro").lower()
        portion_g = max(1, int(round(float(macro_alt.group("portion2").replace(",", ".")))))
        return [PortionItem(food=food, portion_g=portion_g)], MACRO_FIELD_MAP.get(macro, macro)

    macro_match = NL_MACRO_PATTERN.search(raw)
    if macro_match:
        food = macro_match.group("food1").strip(" ?.:,")
        macro = macro_match.group("macro").lower()
        portion_raw = macro_match.group("portion1")
        portion_g = 100
        if portion_raw:
            portion_g = max(1, int(round(float(portion_raw.replace(",", ".")))))
        return [PortionItem(food=food, portion_g=portion_g)], MACRO_FIELD_MAP.get(macro, macro)

    return [], None


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


def _looks_like_lookup(text: str, items: list[PortionItem], *, nl_parsed: bool = False) -> bool:
    if not items:
        return False
    if nl_parsed:
        return True
    if "?" in text:
        return False
    if REASONING_PATTERN.search(text):
        return False
    if len(text) > 120:
        return False
    return True


def parse_intent(text: str) -> ParsedIntent:
    """Parse user input into lookup, compare, substitute, or reasoning intent."""
    raw = _normalize_text(text)
    if not raw:
        return ParsedIntent(kind=IntentKind.REASONING, items=[], raw=raw)

    if COACHING_PATTERN.search(raw) and not NL_CALORIES_PATTERN.search(raw):
        return ParsedIntent(kind=IntentKind.REASONING, items=[], raw=raw)

    parse_compare, parse_substitute = _mobile_intent_modules()

    compare = parse_compare(raw)
    if compare is not None:
        return ParsedIntent(
            kind=IntentKind.COMPARE,
            items=[],
            raw=raw,
            compare=compare,
        )

    substitute = parse_substitute(raw)
    if substitute is not None:
        return ParsedIntent(
            kind=IntentKind.SUBSTITUTE,
            items=[],
            raw=raw,
            substitute=substitute,
        )

    nl_items, highlight = _parse_nl_lookup(raw)
    if nl_items:
        return ParsedIntent(
            kind=IntentKind.LOOKUP,
            items=_apply_household_portions(
                nl_items,
                source_phrases=[raw],
                resolve_phrases=[nl_items[0].food],
            ),
            raw=raw,
            highlight_field=highlight,
        )

    segments = [part.strip() for part in ITEM_SPLIT_PATTERN.split(raw) if part.strip()]
    if not segments:
        segments = [raw]

    items: list[PortionItem] = []
    segment_sources: list[str] = []
    for segment in segments:
        item = _parse_segment(segment)
        if item is not None:
            items.append(item)
            segment_sources.append(segment)

    items = _apply_household_portions(
        items,
        source_phrases=segment_sources,
        resolve_phrases=segment_sources,
    )

    kind = (
        IntentKind.LOOKUP
        if _looks_like_lookup(raw, items)
        else IntentKind.REASONING
    )
    return ParsedIntent(kind=kind, items=items, raw=raw)
