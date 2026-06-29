"""Compare intent patterns for mobile NL queries (N-08-12)."""

from __future__ import annotations

import re
from dataclasses import dataclass

FIELD_ALIASES: dict[str, str] = {
    "proteina": "protein",
    "proteína": "protein",
    "proteínas": "protein",
    "caloria": "kcal",
    "calorias": "kcal",
    "kcal": "kcal",
    "carboidrato": "carb",
    "carboidratos": "carb",
    "gordura": "fat",
    "gorduras": "fat",
    "fibra": "fiber",
    "fibras": "fiber",
}

COMPARE_PATTERNS = [
    re.compile(
        r"qual\s+(?:tem\s+)?mais\s+(?P<field>prote[ií]na|calorias?|carboidratos?|gorduras?|fibras?)"
        r"\s*:?\s*(?P<a>.+?)\s+(?:ou|vs\.?|versus)\s+(?P<b>.+?)\??$",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<a>.+?)\s+(?:ou|vs\.?|versus)\s+(?P<b>.+?)\s*[-—]?\s*"
        r"(?:qual|quem)\s+(?:tem\s+)?mais\s+(?P<field>prote[ií]na|calorias?|carboidratos?|gorduras?|fibras?)\??$",
        re.IGNORECASE,
    ),
    re.compile(
        r"compare\s+(?P<a>.+?)\s+e\s+(?P<b>.+?)\s+(?:em|por)\s+"
        r"(?P<field>prote[ií]na|calorias?|carboidratos?|gorduras?|fibras?)\??$",
        re.IGNORECASE,
    ),
]


@dataclass(frozen=True)
class CompareIntent:
    food_a: str
    food_b: str
    field: str
    portion_g: int = 100


def normalize_field(raw: str) -> str:
    key = raw.strip().lower()
    return FIELD_ALIASES.get(key, key)


def parse_compare(text: str) -> CompareIntent | None:
    cleaned = " ".join(text.strip().split())
    for pattern in COMPARE_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue
        return CompareIntent(
            food_a=match.group("a").strip(" ?.:,"),
            food_b=match.group("b").strip(" ?.:,"),
            field=normalize_field(match.group("field")),
        )
    return None
