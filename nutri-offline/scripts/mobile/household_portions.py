"""Household portion weights — Layer 5 semantic engine (N-09-05).

Business rule BR-PORT-001: household gram weights must come from the portion table
and cite their source in portion metadata — never invent grams at runtime.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from mobile_paths import HOUSEHOLD_PORTIONS_JSON  # noqa: E402

ARTICLE_PATTERN = re.compile(r"^(?:um|uma|uns|umas|1)\s+", re.IGNORECASE)


def normalize_phrase_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


@dataclass(frozen=True)
class HouseholdPortionMatch:
    food: str
    unit: str
    grams: int
    source: str
    default_record_id: str | None = None


class HouseholdPortionResolver:
    def __init__(self, *, entries: list[dict]) -> None:
        self._entries = entries
        self._foods_by_length = sorted(
            ((normalize_phrase_key(entry["food"]), entry) for entry in entries),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    @classmethod
    def from_json(cls, path: Path = HOUSEHOLD_PORTIONS_JSON) -> HouseholdPortionResolver:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(entries=payload["entries"])

    def resolve(self, phrase: str) -> HouseholdPortionMatch | None:
        key = normalize_phrase_key(phrase)
        if not key:
            return None
        key = ARTICLE_PATTERN.sub("", key).strip()
        if not key:
            return None

        for food_key, entry in self._foods_by_length:
            if food_key not in key:
                continue
            units = sorted(entry["units"], key=lambda item: len(normalize_phrase_key(item["unit"])), reverse=True)
            for unit_entry in units:
                unit_key = normalize_phrase_key(unit_entry["unit"])
                if unit_key and unit_key in key:
                    return HouseholdPortionMatch(
                        food=str(entry["food"]),
                        unit=str(unit_entry["unit"]),
                        grams=int(unit_entry["grams"]),
                        source=str(unit_entry["source"]),
                        default_record_id=entry.get("default_record_id"),
                    )
        return None

    def apply_to_food(self, food: str, *, portion_g: int):
        """Return an updated PortionItem when a household unit is detected."""
        from intent_parser import PortionItem  # noqa: E402

        match = self.resolve(food)
        if match is None:
            return None
        return PortionItem(
            food=match.food,
            portion_g=match.grams,
            source_hint=None,
            portion_source=match.source,
        )

    def close(self) -> None:
        return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Resolve household portion (N-09-05)")
    parser.add_argument("phrase", help="Food phrase with household unit")
    parser.add_argument("--json", type=Path, default=HOUSEHOLD_PORTIONS_JSON)
    args = parser.parse_args()

    resolver = HouseholdPortionResolver.from_json(args.json)
    result = resolver.resolve(args.phrase)
    print(
        json.dumps(
            {
                "phrase": args.phrase,
                "food": None if result is None else result.food,
                "grams": None if result is None else result.grams,
                "unit": None if result is None else result.unit,
                "source": None if result is None else result.source,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
