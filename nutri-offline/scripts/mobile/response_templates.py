"""PT-BR response templates for mobile rule engine (N-08-15)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
sys.path.insert(0, str(DATASET_DIR))

from answers import fmt_g, fmt_kcal, scale_nutrient, source_label  # noqa: E402


def format_lookup_prose(
    *,
    name: str,
    source: str,
    portion_g: int,
    metadata: dict[str, Any],
    highlight_field: str | None = None,
) -> str:
    label = source_label(source)
    basis = metadata.get("serving_basis") or "100g"
    kcal = scale_nutrient(metadata.get("energy_kcal"), portion_g, basis=basis)
    protein = scale_nutrient(metadata.get("protein_g"), portion_g, basis=basis)
    carbs = scale_nutrient(metadata.get("carbohydrate_g"), portion_g, basis=basis)
    fat = scale_nutrient(metadata.get("fat_g"), portion_g, basis=basis)
    fiber = scale_nutrient(metadata.get("fiber_g"), portion_g, basis=basis)

    if highlight_field == "fiber" and fiber is not None:
        return (
            f"Segundo a {label}, {portion_g}g de {name} contêm cerca de "
            f"{fmt_g(fiber)}g de fibra."
        )
    if highlight_field == "protein" and protein is not None:
        return (
            f"Segundo a {label}, {portion_g}g de {name} contêm cerca de "
            f"{fmt_g(protein)}g de proteína."
        )

    parts: list[str] = []
    if kcal is not None:
        parts.append(f"{fmt_kcal(kcal)} kcal")
    if protein is not None:
        parts.append(f"{fmt_g(protein)}g de proteína")
    if carbs is not None:
        parts.append(f"{fmt_g(carbs)}g de carboidratos")
    if fat is not None:
        parts.append(f"{fmt_g(fat)}g de gordura")

    joined = ", ".join(parts) if parts else "macros não disponíveis"
    return f"Segundo a {label}, {portion_g}g de {name} contêm aproximadamente {joined}."


def format_compare_answer(
    *,
    winner_name: str,
    loser_name: str,
    field_label: str,
    winner_value: float,
    loser_value: float,
    winner_source: str,
    loser_source: str,
    portion_g: int,
) -> str:
    w_label = source_label(winner_source)
    l_label = source_label(loser_source)
    unit = "kcal" if field_label == "kcal" else "g"
    w_fmt = fmt_kcal(winner_value) if unit == "kcal" else fmt_g(winner_value)
    l_fmt = fmt_kcal(loser_value) if unit == "kcal" else fmt_g(loser_value)
    return (
        f"Comparando {portion_g}g por porção: {winner_name} ({w_label}) tem mais {field_label} "
        f"({w_fmt}{unit}) do que {loser_name} ({l_label}, {l_fmt}{unit})."
    )


def format_substitute_answer(
    *,
    original_name: str,
    substitute_name: str,
    optimize_label: str,
    original_value: float,
    substitute_value: float,
    source: str,
) -> str:
    label = source_label(source)
    return (
        f"Segundo a {label}, {substitute_name} é uma alternativa com menos {optimize_label} "
        f"({fmt_g(substitute_value)}g vs {fmt_g(original_value)}g por 100g) em relação a {original_name}."
    )


def format_not_found(food: str) -> str:
    return (
        f"Não encontrei \"{food}\" no pacote mobile. "
        "Tente um alimento genérico (TACO) ou uma marca popular incluída no índice."
    )


def format_unsupported() -> str:
    return (
        "Consigo ajudar com consultas de macros, comparações simples e substitutos mais leves. "
        "Para orientação nutricional aberta, use a versão desktop com LLM."
    )
