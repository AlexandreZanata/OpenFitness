"""Rule-based compare/substitute engines — no LLM (N-08-14)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(DATASET_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from answers import scale_nutrient  # noqa: E402
from intents_compare import CompareIntent  # noqa: E402
from intents_substitute import SubstituteIntent  # noqa: E402
from lookup_orchestrator import (  # noqa: E402
    MIN_LOOKUP_SCORE,
    _prefer_branded,
    _select_best_hit,
)
from intent_parser import PortionItem  # noqa: E402
from mobile_search import MobileHit, MobileSearcher  # noqa: E402
from response_templates import (  # noqa: E402
    format_compare_answer,
    format_not_found,
    format_substitute_answer,
)


FIELD_TO_METADATA = {
    "protein": ("protein_g", "proteína"),
    "kcal": ("energy_kcal", "calorias"),
    "carb": ("carbohydrate_g", "carboidratos"),
    "fat": ("fat_g", "gordura"),
    "fiber": ("fiber_g", "fibra"),
}


def _mobile_hit_to_rag(hit: MobileHit):
    from rag_pipeline import RagHit

    return RagHit(
        score=hit.score,
        id=hit.id,
        name=hit.name,
        source=hit.source,
        rag_context="",
        metadata=hit.metadata,
    )


def retrieve_mobile_item(searcher: MobileSearcher, food: str, *, portion_g: int = 100) -> MobileHit | None:
    item = PortionItem(food=food, portion_g=portion_g)
    hits = searcher.search(
        item.food,
        top_k=5,
        prefer_branded=_prefer_branded(item),
    )
    rag_hits = [_mobile_hit_to_rag(hit) for hit in hits]
    selected = _select_best_hit(
        rag_hits,
        food=item.food,
        source_hint=item.source_hint,
        min_score=MIN_LOOKUP_SCORE,
        require_overlap=not _prefer_branded(item),
    )
    if selected is None:
        return None
    for hit in hits:
        if hit.id == selected.id:
            return hit
    return None


@dataclass
class ReasoningResult:
    answer: str
    hits: list[MobileHit]
    mode: str


class CompareEngine:
    def __init__(self, searcher: MobileSearcher) -> None:
        self.searcher = searcher

    def execute(self, intent: CompareIntent) -> ReasoningResult:
        hit_a = retrieve_mobile_item(self.searcher, intent.food_a, portion_g=intent.portion_g)
        hit_b = retrieve_mobile_item(self.searcher, intent.food_b, portion_g=intent.portion_g)
        if hit_a is None or hit_b is None:
            missing = intent.food_a if hit_a is None else intent.food_b
            return ReasoningResult(answer=format_not_found(missing), hits=[], mode="compare")

        meta_key, field_label = FIELD_TO_METADATA.get(intent.field, ("energy_kcal", "calorias"))
        basis_a = hit_a.metadata.get("serving_basis") or "100g"
        basis_b = hit_b.metadata.get("serving_basis") or "100g"
        val_a = scale_nutrient(hit_a.metadata.get(meta_key), intent.portion_g, basis=basis_a)
        val_b = scale_nutrient(hit_b.metadata.get(meta_key), intent.portion_g, basis=basis_b)
        if val_a is None or val_b is None:
            return ReasoningResult(
                answer=f"Não há {field_label} disponível para comparar esses alimentos.",
                hits=[hit_a, hit_b],
                mode="compare",
            )

        if val_a >= val_b:
            winner, loser, w_val, l_val = hit_a, hit_b, val_a, val_b
        else:
            winner, loser, w_val, l_val = hit_b, hit_a, val_b, val_a

        answer = format_compare_answer(
            winner_name=winner.name,
            loser_name=loser.name,
            field_label=field_label,
            winner_value=w_val,
            loser_value=l_val,
            winner_source=winner.source,
            loser_source=loser.source,
            portion_g=intent.portion_g,
        )
        return ReasoningResult(answer=answer, hits=[hit_a, hit_b], mode="compare")


class SubstituteEngine:
    def __init__(self, searcher: MobileSearcher) -> None:
        self.searcher = searcher

    def execute(self, intent: SubstituteIntent) -> ReasoningResult:
        original = retrieve_mobile_item(self.searcher, intent.food, portion_g=intent.portion_g)
        if original is None:
            return ReasoningResult(answer=format_not_found(intent.food), hits=[], mode="substitute")

        meta_key, optimize_label = FIELD_TO_METADATA.get(intent.optimize, ("energy_kcal", "calorias"))
        original_value = original.metadata.get(meta_key)
        if original_value is None:
            return ReasoningResult(
                answer=f"Não há {optimize_label} registrados para {original.name}.",
                hits=[original],
                mode="substitute",
            )

        category = original.metadata.get("category") or original.name.split(",")[0]
        candidates = self.searcher.search_category(category, exclude_id=original.id, top_k=30)
        best: MobileHit | None = None
        best_value = float(original_value)
        for candidate in candidates:
            if candidate.source not in {"taco", "tbca"}:
                continue
            value = candidate.metadata.get(meta_key)
            if value is None:
                continue
            if value < best_value:
                best = candidate
                best_value = float(value)

        if best is None:
            return ReasoningResult(
                answer=(
                    f"Não encontrei substituto com menos {optimize_label} que {original.name} "
                    "no pacote mobile."
                ),
                hits=[original],
                mode="substitute",
            )

        answer = format_substitute_answer(
            original_name=original.name,
            substitute_name=best.name,
            optimize_label=optimize_label,
            original_value=float(original_value),
            substitute_value=best_value,
            source=best.source,
        )
        return ReasoningResult(answer=answer, hits=[original, best], mode="substitute")
