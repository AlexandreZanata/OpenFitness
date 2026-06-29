"""Orthographic food token correction — Layer 1 semantic engine (N-09-01).

Business rule BR-NORM-001: apply correction only when edit distance <= 2
and the candidate exists in the mobile spell lexicon.
"""

from __future__ import annotations

import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from mobile_paths import LEXICON_DB  # noqa: E402
from mobile_sqlite import connect  # noqa: E402

BR_NORM_001_MAX_EDIT_DISTANCE = 2

FOOD_STOPWORDS = frozenset({"de", "da", "do", "das", "dos", "e", "com", "sem", "um", "uma"})

MIN_TOKEN_LEN = 3


def normalize_lookup_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def edit_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


@dataclass(frozen=True)
class SpellCorrection:
    original: str
    corrected: str
    edit_distance: int


@dataclass(frozen=True)
class SpellNormalizeResult:
    text: str
    corrections: tuple[SpellCorrection, ...]


def _longest_common_prefix(left: str, right: str) -> int:
    count = 0
    for left_char, right_char in zip(left, right, strict=False):
        if left_char != right_char:
            break
        count += 1
    return count


def build_lexicon_from_sqlite(lexicon_db: Path) -> tuple[frozenset[str], dict[str, int]]:
    connection = connect(str(lexicon_db), readonly=True)
    tokens: set[str] = set()
    frequencies: dict[str, int] = {}

    def _register(raw: str) -> None:
        key = normalize_lookup_key(raw)
        if len(key) < MIN_TOKEN_LEN:
            return
        tokens.add(key)
        frequencies[key] = frequencies.get(key, 0) + 1

    alias_rows = connection.execute("SELECT alias FROM aliases").fetchall()
    for (alias,) in alias_rows:
        _register(alias)

    fts_rows = connection.execute("SELECT search_text, name FROM food_fts").fetchall()
    for search_text, name in fts_rows:
        for raw in (search_text, name):
            for part in str(raw).split():
                _register(part)

    connection.close()
    return frozenset(tokens), frequencies


def _candidate_rank(token: str, word: str, *, distance: int, frequency: int) -> tuple[int, int, int, str]:
    prefix = _longest_common_prefix(token, word)
    return (distance, -prefix, -frequency, word)


def _best_candidate(
    token: str,
    lexicon: frozenset[str],
    frequencies: dict[str, int],
) -> tuple[str | None, int]:
    if token in lexicon:
        return token, 0

    best_word: str | None = None
    best_rank: tuple[int, int, int, str] | None = None
    best_distance = BR_NORM_001_MAX_EDIT_DISTANCE + 1
    token_len = len(token)

    for word in lexicon:
        if abs(len(word) - token_len) > BR_NORM_001_MAX_EDIT_DISTANCE:
            continue
        distance = edit_distance(token, word)
        if distance > BR_NORM_001_MAX_EDIT_DISTANCE:
            continue
        rank = _candidate_rank(token, word, distance=distance, frequency=frequencies.get(word, 0))
        if best_rank is None or rank < best_rank:
            best_rank = rank
            best_distance = distance
            best_word = word

    if best_word is None:
        return None, best_distance
    return best_word, best_distance


class SpellNormalizer:
    def __init__(self, *, lexicon: frozenset[str], frequencies: dict[str, int] | None = None) -> None:
        self._lexicon = lexicon
        self._frequencies = frequencies or {word: 1 for word in lexicon}

    @property
    def lexicon(self) -> frozenset[str]:
        return self._lexicon

    @classmethod
    def from_lexicon_db(cls, lexicon_db: Path = LEXICON_DB) -> SpellNormalizer:
        lexicon, frequencies = build_lexicon_from_sqlite(lexicon_db)
        return cls(lexicon=lexicon, frequencies=frequencies)

    def correct_token(self, token: str) -> tuple[str, SpellCorrection | None]:
        key = normalize_lookup_key(token)
        if len(key) < MIN_TOKEN_LEN:
            return token, None
        if key in FOOD_STOPWORDS:
            return token, None

        candidate, distance = _best_candidate(key, self._lexicon, self._frequencies)
        if candidate is None or distance == 0:
            return token, None

        return candidate, SpellCorrection(original=key, corrected=candidate, edit_distance=distance)

    def normalize_food(self, phrase: str) -> SpellNormalizeResult:
        raw_tokens = phrase.strip().split()
        if not raw_tokens:
            return SpellNormalizeResult(text="", corrections=())

        leading_skip = 0
        while leading_skip < len(raw_tokens):
            if normalize_lookup_key(raw_tokens[leading_skip]) in FOOD_STOPWORDS:
                leading_skip += 1
            else:
                break

        corrected_tokens: list[str] = []
        corrections: list[SpellCorrection] = []
        for index, token in enumerate(raw_tokens):
            if index < leading_skip:
                continue
            fixed, correction = self.correct_token(token)
            corrected_tokens.append(fixed)
            if correction is not None:
                corrections.append(correction)

        return SpellNormalizeResult(text=" ".join(corrected_tokens), corrections=tuple(corrections))

    def close(self) -> None:
        return None


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Spell-normalize a food phrase (N-09-01)")
    parser.add_argument("phrase", help="Food phrase to normalize")
    parser.add_argument("--lexicon-db", type=Path, default=LEXICON_DB)
    args = parser.parse_args()

    if not args.lexicon_db.is_file():
        print(f"ERROR: lexicon db missing: {args.lexicon_db}", file=sys.stderr)
        return 1

    normalizer = SpellNormalizer.from_lexicon_db(args.lexicon_db)
    result = normalizer.normalize_food(args.phrase)
    print(
        json.dumps(
            {
                "input": args.phrase,
                "normalized": result.text,
                "corrections": [
                    {
                        "original": item.original,
                        "corrected": item.corrected,
                        "edit_distance": item.edit_distance,
                    }
                    for item in result.corrections
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
