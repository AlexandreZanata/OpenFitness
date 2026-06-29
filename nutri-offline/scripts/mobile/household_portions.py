"""Household portion weights — Layer 5 semantic engine (N-09-05).

Business rule BR-PORT-001: household gram weights must come from the portion table
and cite their source in portion metadata — never invent grams at runtime.

Business rule BR-PORT-002: when a phrase is article-only (``um|uma|1 <food>``) or a
bare food name with no explicit gram portion, apply the entry ``default_unit`` grams.
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
        indexed: list[tuple[str, dict]] = []
        for entry in entries:
            keys = [normalize_phrase_key(entry["food"])]
            for alias in entry.get("aliases", []):
                keys.append(normalize_phrase_key(str(alias)))
            for key in keys:
                indexed.append((key, entry))
        self._foods_by_length = sorted(indexed, key=lambda item: len(item[0]), reverse=True)

    @classmethod
    def from_json(cls, path: Path = HOUSEHOLD_PORTIONS_JSON) -> HouseholdPortionResolver:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(entries=payload["entries"])

    def _unit_entries(self, entry: dict) -> list[dict]:
        return sorted(
            entry["units"],
            key=lambda item: len(normalize_phrase_key(item["unit"])),
            reverse=True,
        )

    def _match_from_unit(self, entry: dict, unit_entry: dict) -> HouseholdPortionMatch:
        return HouseholdPortionMatch(
            food=str(entry["food"]),
            unit=str(unit_entry["unit"]),
            grams=int(unit_entry["grams"]),
            source=str(unit_entry["source"]),
            default_record_id=entry.get("default_record_id"),
        )

    def _find_unit(self, entry: dict, unit_name: str) -> dict | None:
        unit_key = normalize_phrase_key(unit_name)
        for unit_entry in entry["units"]:
            if normalize_phrase_key(unit_entry["unit"]) == unit_key:
                return unit_entry
        return None

    def _resolve_explicit_unit(self, key: str) -> HouseholdPortionMatch | None:
        for food_key, entry in self._foods_by_length:
            if food_key not in key:
                continue
            for unit_entry in self._unit_entries(entry):
                unit_key = normalize_phrase_key(unit_entry["unit"])
                if unit_key and unit_key in key:
                    return self._match_from_unit(entry, unit_entry)
        return None

    def _resolve_default_unit(self, key: str) -> HouseholdPortionMatch | None:
        for food_key, entry in self._foods_by_length:
            default_unit = entry.get("default_unit")
            if not default_unit or key != food_key:
                continue
            unit_entry = self._find_unit(entry, str(default_unit))
            if unit_entry is None:
                continue
            return self._match_from_unit(entry, unit_entry)
        return None

    def resolve(self, phrase: str) -> HouseholdPortionMatch | None:
        key = normalize_phrase_key(phrase)
        if not key:
            return None

        explicit = self._resolve_explicit_unit(key)
        if explicit is not None:
            return explicit

        stripped = ARTICLE_PATTERN.sub("", key).strip()
        if not stripped:
            return None

        explicit_stripped = self._resolve_explicit_unit(stripped)
        if explicit_stripped is not None:
            return explicit_stripped

        return self._resolve_default_unit(stripped)

    def apply_to_food(self, food: str, *, portion_g: int, source_phrase: str | None = None):
        """Return an updated PortionItem when a household unit is detected."""
        from intent_parser import PortionItem  # noqa: E402

        phrase = source_phrase if source_phrase is not None else food
        match = self.resolve(phrase)
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
