"""Substitute intent patterns for mobile NL queries (N-08-13)."""

from __future__ import annotations

import re
from dataclasses import dataclass

SUBSTITUTE_PATTERNS = [
    re.compile(
        r"(?:existe|tem|h[aá])\s+(?:alguma\s+)?(?:op[cç][aã]o|alternativa|substituto)\s+"
        r"(?:mais\s+)?(?P<opt>leve|saud[aá]vel|light)\s+(?:que|para)\s+(?P<food>.+?)\??$",
        re.IGNORECASE,
    ),
    re.compile(
        r"substituto\s+(?:mais\s+)?(?P<opt>leve|light|saud[aá]vel)\s+(?:para|de)\s+(?P<food>.+?)\??$",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?P<food>.+?)\s+(?:com\s+)?menos\s+(?P<opt>carboidratos?|calorias?|gorduras?)\??$",
        re.IGNORECASE,
    ),
    re.compile(
        r"alternativa\s+(?:com\s+)?menos\s+(?P<opt>carboidratos?|calorias?|gorduras?)\s+(?:que|para)\s+(?P<food>.+?)\??$",
        re.IGNORECASE,
    ),
]

OPTIMIZE_MAP = {
    "leve": "kcal",
    "light": "kcal",
    "saudavel": "kcal",
    "saudável": "kcal",
    "carboidrato": "carb",
    "carboidratos": "carb",
    "caloria": "kcal",
    "calorias": "kcal",
    "gordura": "fat",
    "gorduras": "fat",
}


@dataclass(frozen=True)
class SubstituteIntent:
    food: str
    optimize: str
    portion_g: int = 100


def parse_substitute(text: str) -> SubstituteIntent | None:
    cleaned = " ".join(text.strip().split())
    for pattern in SUBSTITUTE_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue
        opt = match.group("opt").strip().lower()
        food = match.group("food").strip(" ?.:,")
        optimize = OPTIMIZE_MAP.get(opt, opt)
        if optimize not in {"kcal", "carb", "fat"}:
            optimize = "kcal"
        return SubstituteIntent(food=food, optimize=optimize)
    return None
