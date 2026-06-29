"""Food category ontology resolution — Layer 3 semantic engine (N-09-03).

Business rule BR-NORM-003: category phrases resolve through the ontology map
before vector search. When multiple candidates exist and macros may differ, the
default record is used and a clarify note is attached to the response metadata.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from synonym_resolver import normalize_phrase_key  # noqa: E402

FOOD_ONTOLOGY_JSON = Path(__file__).resolve().parents[2] / "config" / "semantic" / "food_ontology.json"


@dataclass(frozen=True)
class OntologyMatch:
    node_id: str
    phrase: str
    label: str
    default_record_id: str
    default_label: str | None
    candidate_record_ids: tuple[str, ...]
    clarify_when_macros_differ: bool


@dataclass(frozen=True)
class OntologyResolveResult:
    phrase: str
    match: OntologyMatch | None
    needs_clarify: bool = False

    @property
    def clarify_note(self) -> str | None:
        if not self.needs_clarify or self.match is None:
            return None
        label = self.match.default_label or self.match.label
        return (
            f"Nota: '{self.phrase}' abrange vários alimentos da categoria "
            f"({self.match.label}). Valores para {label}."
        )


def _index_nodes(nodes: list[dict]) -> dict[str, OntologyMatch]:
    indexed: dict[str, OntologyMatch] = {}
    for node in nodes:
        match = OntologyMatch(
            node_id=str(node["id"]),
            phrase="",
            label=str(node["label"]),
            default_record_id=str(node["default_record_id"]),
            default_label=node.get("default_label"),
            candidate_record_ids=tuple(str(item) for item in node["candidate_record_ids"]),
            clarify_when_macros_differ=bool(node.get("clarify_when_macros_differ", False)),
        )
        for phrase in node["phrases"]:
            indexed[normalize_phrase_key(phrase)] = OntologyMatch(
                node_id=match.node_id,
                phrase=normalize_phrase_key(phrase),
                label=match.label,
                default_record_id=match.default_record_id,
                default_label=match.default_label,
                candidate_record_ids=match.candidate_record_ids,
                clarify_when_macros_differ=match.clarify_when_macros_differ,
            )
    return indexed


class OntologyResolver:
    def __init__(self, *, phrase_index: dict[str, OntologyMatch]) -> None:
        self._phrase_index = phrase_index
        self._phrases_by_length = sorted(phrase_index.keys(), key=len, reverse=True)

    @classmethod
    def from_json(cls, path: Path = FOOD_ONTOLOGY_JSON) -> OntologyResolver:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(phrase_index=_index_nodes(payload["nodes"]))

    def resolve(self, phrase: str) -> OntologyResolveResult:
        key = normalize_phrase_key(phrase)
        if not key:
            return OntologyResolveResult(phrase=phrase, match=None)

        exact = self._phrase_index.get(key)
        if exact is not None:
            return self._result_for_match(phrase, exact)

        for candidate_phrase in self._phrases_by_length:
            if key == candidate_phrase or candidate_phrase in key or key in candidate_phrase:
                return self._result_for_match(phrase, self._phrase_index[candidate_phrase])

        return OntologyResolveResult(phrase=phrase, match=None)

    @staticmethod
    def _result_for_match(phrase: str, match: OntologyMatch) -> OntologyResolveResult:
        needs_clarify = match.clarify_when_macros_differ and len(match.candidate_record_ids) > 1
        return OntologyResolveResult(phrase=phrase, match=match, needs_clarify=needs_clarify)

    def close(self) -> None:
        return None


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Resolve a food phrase via ontology (N-09-03)")
    parser.add_argument("phrase", help="Food phrase to resolve")
    parser.add_argument("--json", type=Path, default=FOOD_ONTOLOGY_JSON)
    args = parser.parse_args()

    resolver = OntologyResolver.from_json(args.json)
    result = resolver.resolve(args.phrase)
    print(
        json.dumps(
            {
                "phrase": args.phrase,
                "node_id": None if result.match is None else result.match.node_id,
                "default_record_id": None if result.match is None else result.match.default_record_id,
                "candidates": [] if result.match is None else list(result.match.candidate_record_ids),
                "needs_clarify": result.needs_clarify,
                "clarify_note": result.clarify_note,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
