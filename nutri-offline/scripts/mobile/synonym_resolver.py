"""Colloquial phrase → canonical record resolution — Layer 2 semantic engine (N-09-02).

Business rule BR-NORM-002: synonym lookup runs after spell-fix and before vector
search. When multiple candidates exist, the default record is returned with an
explicit label in match metadata.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from mobile_paths import SYNONYMS_DB  # noqa: E402
from mobile_sqlite import connect  # noqa: E402


def normalize_phrase_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


@dataclass(frozen=True)
class SynonymMatch:
    phrase: str
    record_id: str
    canonical_name: str
    source: str
    label: str | None
    priority: int
    is_default: bool


@dataclass(frozen=True)
class SynonymResolveResult:
    phrase: str
    matches: tuple[SynonymMatch, ...]

    @property
    def primary(self) -> SynonymMatch | None:
        if not self.matches:
            return None
        for match in self.matches:
            if match.is_default:
                return match
        return self.matches[0]


class SynonymResolver:
    def __init__(self, *, db_path: Path | None = None) -> None:
        self._db_path = db_path

    @classmethod
    def from_manual_json(cls, path: Path) -> SynonymResolver:
        entries = json.loads(path.read_text(encoding="utf-8"))["entries"]
        resolver = cls(db_path=None)
        resolver._manual_index = _index_manual_entries(entries)
        return resolver

    @classmethod
    def from_db(cls, db_path: Path = SYNONYMS_DB) -> SynonymResolver:
        return cls(db_path=db_path)

    def resolve(self, phrase: str) -> SynonymResolveResult:
        key = normalize_phrase_key(phrase)
        if not key:
            return SynonymResolveResult(phrase=phrase, matches=())

        manual_index = getattr(self, "_manual_index", None)
        if manual_index is not None:
            return SynonymResolveResult(phrase=phrase, matches=manual_index.get(key, ()))

        if self._db_path is None or not self._db_path.is_file():
            return SynonymResolveResult(phrase=phrase, matches=())

        connection = connect(str(self._db_path), readonly=True)
        rows = connection.execute(
            """
            SELECT phrase, record_id, canonical_name, source, priority, label, is_default
            FROM synonym_map
            WHERE phrase = ?
            ORDER BY is_default DESC, priority, record_id
            """,
            (key,),
        ).fetchall()
        connection.close()
        matches = tuple(
            SynonymMatch(
                phrase=str(row[0]),
                record_id=str(row[1]),
                canonical_name=str(row[2]),
                source=str(row[3]),
                label=str(row[5]) if row[5] else None,
                priority=int(row[4]),
                is_default=bool(row[6]),
            )
            for row in rows
        )
        return SynonymResolveResult(phrase=phrase, matches=matches)

    def close(self) -> None:
        return None


def _index_manual_entries(entries: list[dict]) -> dict[str, tuple[SynonymMatch, ...]]:
    grouped: dict[str, list[SynonymMatch]] = {}
    for entry in entries:
        phrase = normalize_phrase_key(entry["phrase"])
        default_id = entry["default_record_id"]
        label = entry.get("label")
        for index, record_id in enumerate(entry["candidates"]):
            match = SynonymMatch(
                phrase=phrase,
                record_id=record_id,
                canonical_name=record_id,
                source="manual",
                label=label,
                priority=index,
                is_default=record_id == default_id,
            )
            grouped.setdefault(phrase, []).append(match)
    return {phrase: tuple(sorted(items, key=lambda item: (not item.is_default, item.priority))) for phrase, items in grouped.items()}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Resolve a colloquial food phrase (N-09-02)")
    parser.add_argument("phrase", help="Food phrase to resolve")
    parser.add_argument("--db", type=Path, default=SYNONYMS_DB)
    args = parser.parse_args()

    if not args.db.is_file():
        print(f"ERROR: synonyms db missing: {args.db}", file=sys.stderr)
        return 1

    resolver = SynonymResolver.from_db(args.db)
    result = resolver.resolve(args.phrase)
    print(
        json.dumps(
            {
                "phrase": args.phrase,
                "primary": None
                if result.primary is None
                else {
                    "record_id": result.primary.record_id,
                    "label": result.primary.label,
                    "is_default": result.primary.is_default,
                },
                "candidates": [
                    {
                        "record_id": match.record_id,
                        "label": match.label,
                        "is_default": match.is_default,
                    }
                    for match in result.matches
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
