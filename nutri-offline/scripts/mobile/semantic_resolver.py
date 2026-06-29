"""Semantic food query pipeline — orchestrates layers 1–3 (N-09-06).

Layers 4 (multi-surface vectors) and 5 (household portions) run in index build
and intent parsing respectively; this resolver unifies spell-fix, synonyms,
and ontology before hybrid vector search.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mobile_paths import FOOD_ONTOLOGY_JSON, LEXICON_DB, SYNONYMS_DB  # noqa: E402
from ontology_resolver import OntologyResolver  # noqa: E402
from spell_normalize import SpellNormalizer  # noqa: E402
from synonym_resolver import SynonymResolver  # noqa: E402


@dataclass(frozen=True)
class SemanticResolution:
    original: str
    normalized: str
    overlap_food: str
    primary_layer: str | None
    layers: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def to_debug_dict(self) -> dict[str, Any]:
        return {
            "original": self.original,
            "normalized": self.normalized,
            "overlap_food": self.overlap_food,
            "primary_layer": self.primary_layer,
            "layers": list(self.layers),
        }


class SemanticResolver:
    def __init__(
        self,
        *,
        spell_normalizer: SpellNormalizer | None = None,
        synonym_resolver: SynonymResolver | None = None,
        ontology_resolver: OntologyResolver | None = None,
    ) -> None:
        self._spell = spell_normalizer
        if self._spell is None and LEXICON_DB.is_file():
            self._spell = SpellNormalizer.from_lexicon_db(LEXICON_DB)
        self._synonym = synonym_resolver
        if self._synonym is None and SYNONYMS_DB.is_file():
            self._synonym = SynonymResolver.from_db(SYNONYMS_DB)
        self._ontology = ontology_resolver
        if self._ontology is None and FOOD_ONTOLOGY_JSON.is_file():
            self._ontology = OntologyResolver.from_json(FOOD_ONTOLOGY_JSON)
        self._last_resolution: SemanticResolution | None = None

    @property
    def last_resolution(self) -> SemanticResolution | None:
        return self._last_resolution

    def resolve(self, food: str) -> SemanticResolution:
        layers: list[dict[str, str]] = []
        normalized = food

        if self._spell is not None:
            spell_result = self._spell.normalize_food(food)
            normalized = spell_result.text
            for correction in spell_result.corrections:
                layers.append(
                    {
                        "layer": "spell",
                        "original": correction.original,
                        "corrected": correction.corrected,
                        "edit_distance": str(correction.edit_distance),
                    }
                )

        primary_layer: str | None = None
        overlap_food = normalized

        if self._synonym is not None:
            synonym_result = self._synonym.resolve(normalized)
            if synonym_result.primary is not None:
                primary = synonym_result.primary
                primary_layer = "synonym"
                layers.append(
                    {
                        "layer": "synonym",
                        "record_id": primary.record_id,
                        "label": primary.label or "",
                    }
                )
        if primary_layer is None and self._ontology is not None:
            ontology_result = self._ontology.resolve(normalized)
            if ontology_result.match is not None:
                match = ontology_result.match
                primary_layer = "ontology"
                layers.append(
                    {
                        "layer": "ontology",
                        "node_id": match.node_id,
                        "record_id": match.default_record_id,
                        "label": match.default_label or match.label,
                    }
                )
        if primary_layer is None and any(layer["layer"] == "spell" for layer in layers):
            primary_layer = "spell"

        resolution = SemanticResolution(
            original=food,
            normalized=normalized,
            overlap_food=overlap_food,
            primary_layer=primary_layer,
            layers=tuple(layers),
        )
        self._last_resolution = resolution
        return resolution

    def close(self) -> None:
        return None


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Semantic resolver pipeline (layers 1–3)")
    parser.add_argument("food", help="Food phrase to resolve")
    parser.add_argument("--json", action="store_true", help="Print JSON debug payload")
    args = parser.parse_args(argv)

    resolver = SemanticResolver()
    result = resolver.resolve(args.food)
    if args.json:
        print(json.dumps(result.to_debug_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"normalized: {result.normalized}")
        print(f"primary_layer: {result.primary_layer}")
        for layer in result.layers:
            print(f"  {layer['layer']}: {layer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
