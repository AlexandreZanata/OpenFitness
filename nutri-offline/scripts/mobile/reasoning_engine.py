"""Rule-based compare/substitute engines — no LLM (N-08-14, desktop parity)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

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
from rag_pipeline import RagHit  # noqa: E402
from response_templates import (  # noqa: E402
    format_compare_answer,
    format_not_found,
    format_substitute_answer,
)
from substitute_rules import (  # noqa: E402
    is_blocked_substitute_name,
    is_staple_candidate_name,
    load_substitute_rules,
    resolve_staple_group,
    staple_preference_score,
    within_kcal_band,
)


FIELD_TO_METADATA = {
    "protein": ("protein_g", "proteína"),
    "kcal": ("energy_kcal", "calorias"),
    "carb": ("carbohydrate_g", "carboidratos"),
    "fat": ("fat_g", "gordura"),
    "fiber": ("fiber_g", "fibra"),
}


@dataclass
class ReasoningHit:
    score: float
    id: str
    name: str
    source: str
    metadata: dict[str, Any]


class ReasoningSearcher(Protocol):
    def search(
        self,
        food: str,
        *,
        top_k: int = 5,
        source_hint: str | None = None,
        prefer_branded: bool = False,
    ) -> list[ReasoningHit]: ...

    def search_staple_candidates(
        self,
        *,
        exclude_id: str | None = None,
    ) -> list[ReasoningHit]: ...

    def search_category(
        self,
        category: str,
        *,
        exclude_id: str | None = None,
        top_k: int = 30,
    ) -> list[ReasoningHit]: ...


def _to_rag_hit(hit: ReasoningHit) -> RagHit:
    return RagHit(
        score=hit.score,
        id=hit.id,
        name=hit.name,
        source=hit.source,
        rag_context="",
        metadata=hit.metadata,
    )


def retrieve_reasoning_item(
    searcher: ReasoningSearcher,
    food: str,
    *,
    portion_g: int = 100,
) -> ReasoningHit | None:
    item = PortionItem(food=food, portion_g=portion_g)
    hits = searcher.search(
        item.food,
        top_k=5,
        prefer_branded=_prefer_branded(item),
    )
    rag_hits = [_to_rag_hit(hit) for hit in hits]
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
    hits: list[ReasoningHit]
    mode: str


class CompareEngine:
    def __init__(self, searcher: ReasoningSearcher, *, catalog: str = "mobile") -> None:
        self.searcher = searcher
        self._catalog = catalog

    def execute(self, intent: CompareIntent) -> ReasoningResult:
        hit_a = retrieve_reasoning_item(self.searcher, intent.food_a, portion_g=intent.portion_g)
        hit_b = retrieve_reasoning_item(self.searcher, intent.food_b, portion_g=intent.portion_g)
        if hit_a is None or hit_b is None:
            missing = intent.food_a if hit_a is None else intent.food_b
            return ReasoningResult(
                answer=format_not_found(missing, catalog=self._catalog),
                hits=[],
                mode="compare",
            )

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
    def __init__(self, searcher: ReasoningSearcher, *, catalog: str = "mobile") -> None:
        self.searcher = searcher
        self._catalog = catalog
        self._rules = load_substitute_rules()

    def _collect_candidates(self, *, food: str, original: ReasoningHit) -> list[ReasoningHit]:
        staple_group = resolve_staple_group(
            food_query=food,
            original_name=original.name,
            rules=self._rules,
        )
        if staple_group is not None:
            pool = self.searcher.search_staple_candidates(exclude_id=original.id)
            return [
                candidate
                for candidate in pool
                if is_staple_candidate_name(candidate.name, staple_group)
            ]

        category = original.metadata.get("category") or original.name.split(",")[0]
        return self.searcher.search_category(category, exclude_id=original.id, top_k=30)

    def _rank_substitute(
        self,
        *,
        candidates: list[ReasoningHit],
        original_value: float,
        optimize: str,
        original_kcal: float | None,
    ) -> tuple[ReasoningHit | None, float | None]:
        band_pct = float(self._rules.get("kcal_band_pct", 30))
        best: ReasoningHit | None = None
        best_rank: tuple[float, float] | None = None
        best_in_band: ReasoningHit | None = None
        best_in_band_rank: tuple[float, float] | None = None

        for candidate in candidates:
            if candidate.source not in {"taco", "tbca"}:
                continue
            value = candidate.metadata.get(
                FIELD_TO_METADATA.get(optimize, ("energy_kcal", "calorias"))[0]
            )
            if value is None or value >= original_value:
                continue

            pref = staple_preference_score(candidate.name)
            rank = (float(value), -pref)

            if best_rank is None or rank < best_rank:
                best = candidate
                best_rank = rank

            if optimize == "kcal" and original_kcal is not None:
                if within_kcal_band(
                    original_kcal=float(original_kcal),
                    candidate_kcal=float(value),
                    band_pct=band_pct,
                ) and (best_in_band_rank is None or rank < best_in_band_rank):
                    best_in_band = candidate
                    best_in_band_rank = rank

        if optimize == "kcal" and best_in_band is not None:
            return best_in_band, best_in_band_rank[0] if best_in_band_rank else None
        return best, best_rank[0] if best_rank else None

    def execute(self, intent: SubstituteIntent) -> ReasoningResult:
        original = retrieve_reasoning_item(self.searcher, intent.food, portion_g=intent.portion_g)
        if original is None:
            return ReasoningResult(
                answer=format_not_found(intent.food, catalog=self._catalog),
                hits=[],
                mode="substitute",
            )

        meta_key, optimize_label = FIELD_TO_METADATA.get(intent.optimize, ("energy_kcal", "calorias"))
        original_value = original.metadata.get(meta_key)
        if original_value is None:
            return ReasoningResult(
                answer=f"Não há {optimize_label} registrados para {original.name}.",
                hits=[original],
                mode="substitute",
            )

        staple_group = resolve_staple_group(
            food_query=intent.food,
            original_name=original.name,
            rules=self._rules,
        )
        candidates = self._collect_candidates(food=intent.food, original=original)
        if staple_group is not None:
            candidates = [
                candidate
                for candidate in candidates
                if not is_blocked_substitute_name(candidate.name, staple_group)
            ]

        best, best_value = self._rank_substitute(
            candidates=candidates,
            original_value=float(original_value),
            optimize=intent.optimize,
            original_kcal=original.metadata.get("energy_kcal"),
        )

        if best is None or best_value is None:
            scope = "catálogo indexado" if self._catalog == "desktop" else "pacote mobile"
            return ReasoningResult(
                answer=(
                    f"Não encontrei substituto com menos {optimize_label} que {original.name} "
                    f"no {scope}."
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


# Backward-compatible alias for mobile tests
MobileHit = ReasoningHit


def _mobile_hit_to_rag(hit: ReasoningHit) -> RagHit:
    return _to_rag_hit(hit)


def retrieve_mobile_item(searcher: ReasoningSearcher, food: str, *, portion_g: int = 100) -> ReasoningHit | None:
    return retrieve_reasoning_item(searcher, food, portion_g=portion_g)
