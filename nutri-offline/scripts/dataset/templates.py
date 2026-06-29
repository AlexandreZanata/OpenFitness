"""Question templates for NutriOffline fine-tuning dataset (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

TemplateFormatter = Callable[..., str]


@dataclass(frozen=True)
class QuestionTemplate:
    template_id: str
    category: str
    language: str
    format_question: TemplateFormatter


def _pt_direct_1(food_name: str, source: str, **_kwargs: object) -> str:
    return f"Quantas calorias tem {food_name} por 100g segundo a {source}?"


def _pt_direct_2(food_name: str, **_kwargs: object) -> str:
    return f"Qual o valor energético de {food_name} por 100g?"


def _pt_direct_3(food_name: str, source: str, **_kwargs: object) -> str:
    return f"Me diga os macronutrientes de {food_name} ({source})."


def _pt_direct_4(food_name: str, **_kwargs: object) -> str:
    return f"Quantos gramas de proteína tem {food_name} em 100g?"


def _pt_direct_5(food_name: str, source: str, **_kwargs: object) -> str:
    return f"De acordo com a {source}, qual a composição nutricional de {food_name}?"


def _en_direct_1(food_name: str, source: str, **_kwargs: object) -> str:
    return f"How many calories are in 100g of {food_name} according to {source}?"


def _en_direct_2(food_name: str, **_kwargs: object) -> str:
    return f"What are the macronutrients of {food_name} per 100g?"


def _pt_portion_1(food_name: str, portion_g: int, source: str, **_kwargs: object) -> str:
    return f"Quantas calorias tem {portion_g}g de {food_name} segundo a {source}?"


def _pt_portion_2(food_name: str, portion_g: int, **_kwargs: object) -> str:
    return f"Se eu comer {portion_g}g de {food_name}, quantas calorias consumo?"


def _pt_portion_3(food_name: str, portion_g: int, source: str, **_kwargs: object) -> str:
    return f"Calcule os macronutrientes para uma porção de {portion_g}g de {food_name} ({source})."


def _pt_portion_4(food_name: str, portion_g: int, **_kwargs: object) -> str:
    return f"Quanto de carboidrato tem em {portion_g}g de {food_name}?"


def _pt_portion_5(food_name: str, portion_g: int, source: str, **_kwargs: object) -> str:
    return f"Porção de {portion_g}g de {food_name}: qual o total de kcal e proteínas?"


def _en_portion_1(food_name: str, portion_g: int, source: str, **_kwargs: object) -> str:
    return f"How many calories are in {portion_g}g of {food_name} according to {source}?"


def _pt_compare_1(food_a: str, food_b: str, nutrient: str, **_kwargs: object) -> str:
    return f"Qual tem mais {nutrient}, {food_a} ou {food_b}?"


def _pt_compare_2(food_a: str, food_b: str, source: str, **_kwargs: object) -> str:
    return f"Compare as calorias de {food_a} e {food_b} segundo a {source}."


def _pt_compare_3(food_a: str, food_b: str, **_kwargs: object) -> str:
    return f"Entre {food_a} e {food_b}, qual é mais rico em proteína por 100g?"


def _pt_compare_4(food_a: str, food_b: str, **_kwargs: object) -> str:
    return f"Qual alimento tem menos gordura: {food_a} ou {food_b}?"


def _pt_compare_5(food_a: str, food_b: str, source: str, **_kwargs: object) -> str:
    return f"De acordo com a {source}, qual tem mais carboidrato: {food_a} ou {food_b}?"


def _en_compare_1(food_a: str, food_b: str, nutrient: str, **_kwargs: object) -> str:
    return f"Which has more {nutrient}, {food_a} or {food_b}?"


def _pt_subst_1(food_name: str, alt_name: str, **_kwargs: object) -> str:
    return f"O que posso usar no lugar de {food_name} para reduzir carboidratos?"


def _pt_subst_2(food_name: str, alt_name: str, source: str, **_kwargs: object) -> str:
    return f"Qual alternativa com menos carboidrato que {food_name}? ({source})"


def _pt_subst_3(food_name: str, alt_name: str, **_kwargs: object) -> str:
    return f"Preciso substituir {food_name} por algo com menos carboidrato. Alguma sugestão?"


def _pt_subst_4(food_name: str, alt_name: str, **_kwargs: object) -> str:
    return f"Existe opção mais leve em carboidratos que {food_name}?"


def _pt_subst_5(food_name: str, alt_name: str, source: str, **_kwargs: object) -> str:
    return f"Segundo a {source}, qual alimento substitui {food_name} com menos carboidratos?"


def _pt_allergen_1(food_name: str, allergen: str, **_kwargs: object) -> str:
    return f"O produto {food_name} contém {allergen}?"


def _pt_allergen_2(food_name: str, allergen: str, **_kwargs: object) -> str:
    return f"{food_name} tem {allergen} nos ingredientes?"


def _pt_allergen_3(food_name: str, allergen: str, source: str, **_kwargs: object) -> str:
    return f"De acordo com a {source}, {food_name} contém {allergen}?"


def _pt_allergen_4(food_name: str, allergen: str, **_kwargs: object) -> str:
    return f"Posso consumir {food_name} se tenho alergia a {allergen}?"


def _pt_allergen_5(food_name: str, allergen: str, source: str, **_kwargs: object) -> str:
    return f"Verifique na {source} se {food_name} possui {allergen}."


def _pt_reason_1(food_name: str, source: str, **_kwargs: object) -> str:
    return f"Explique o índice glicêmico aproximado de {food_name} com base nos dados da {source}."


def _pt_reason_2(food_name: str, **_kwargs: object) -> str:
    return f"{food_name} é adequado para uma dieta com foco em saciedade? Use os macros disponíveis."


def _pt_reason_3(food_name: str, source: str, **_kwargs: object) -> str:
    return f"Com base na {source}, {food_name} é mais rico em carboidrato ou proteína?"


def _pt_reason_4(food_name: str, **_kwargs: object) -> str:
    return f"Analise a densidade calórica de {food_name} por 100g."


def _pt_reason_5(food_name: str, source: str, **_kwargs: object) -> str:
    return f"Usando os dados da {source}, {food_name} é uma boa fonte de fibras?"


def _en_reason_1(food_name: str, source: str, **_kwargs: object) -> str:
    return f"Explain the approximate glycemic impact of {food_name} using {source} data."


def _pt_unknown_1(food_name: str, **_kwargs: object) -> str:
    return f"Quantas calorias tem 100g de {food_name}?"


def _pt_unknown_2(food_name: str, **_kwargs: object) -> str:
    return f"Qual o valor proteico de {food_name}?"


def _pt_unknown_3(food_name: str, **_kwargs: object) -> str:
    return f"Informe os macros de {food_name} segundo a TACO."


def _pt_unknown_4(food_name: str, **_kwargs: object) -> str:
    return f"Me diga a composição nutricional de {food_name}."


def _pt_unknown_5(food_name: str, **_kwargs: object) -> str:
    return f"Existe {food_name} na tabela TACO?"


def _en_unknown_1(food_name: str, **_kwargs: object) -> str:
    return f"How many calories are in 100g of {food_name}?"


def _pt_household_1(food_name: str, unit_label: str, **_kwargs: object) -> str:
    return f"Quantas calorias tem {unit_label} de {food_name}?"


def _pt_household_2(food_name: str, unit_label: str, **_kwargs: object) -> str:
    return f"Quanto de proteína tem {unit_label} de {food_name}?"


def _pt_household_3(food_name: str, unit_label: str, source: str, **_kwargs: object) -> str:
    return f"Segundo a {source}, quantas calorias tem {unit_label} de {food_name}?"


def _pt_household_4(food_name: str, unit_label: str, **_kwargs: object) -> str:
    return f"Qual a porção caseira de {food_name} em gramas e calorias?"


def _pt_household_5(food_name: str, unit_label: str, **_kwargs: object) -> str:
    return f"Calcule os nutrientes para {unit_label} de {food_name}."


TEMPLATES: list[QuestionTemplate] = [
    QuestionTemplate("direct_pt_1", "direct_lookup", "pt", _pt_direct_1),
    QuestionTemplate("direct_pt_2", "direct_lookup", "pt", _pt_direct_2),
    QuestionTemplate("direct_pt_3", "direct_lookup", "pt", _pt_direct_3),
    QuestionTemplate("direct_pt_4", "direct_lookup", "pt", _pt_direct_4),
    QuestionTemplate("direct_pt_5", "direct_lookup", "pt", _pt_direct_5),
    QuestionTemplate("direct_en_1", "direct_lookup", "en", _en_direct_1),
    QuestionTemplate("direct_en_2", "direct_lookup", "en", _en_direct_2),
    QuestionTemplate("portion_pt_1", "portion_math", "pt", _pt_portion_1),
    QuestionTemplate("portion_pt_2", "portion_math", "pt", _pt_portion_2),
    QuestionTemplate("portion_pt_3", "portion_math", "pt", _pt_portion_3),
    QuestionTemplate("portion_pt_4", "portion_math", "pt", _pt_portion_4),
    QuestionTemplate("portion_pt_5", "portion_math", "pt", _pt_portion_5),
    QuestionTemplate("portion_en_1", "portion_math", "en", _en_portion_1),
    QuestionTemplate("compare_pt_1", "comparison", "pt", _pt_compare_1),
    QuestionTemplate("compare_pt_2", "comparison", "pt", _pt_compare_2),
    QuestionTemplate("compare_pt_3", "comparison", "pt", _pt_compare_3),
    QuestionTemplate("compare_pt_4", "comparison", "pt", _pt_compare_4),
    QuestionTemplate("compare_pt_5", "comparison", "pt", _pt_compare_5),
    QuestionTemplate("compare_en_1", "comparison", "en", _en_compare_1),
    QuestionTemplate("subst_pt_1", "substitution", "pt", _pt_subst_1),
    QuestionTemplate("subst_pt_2", "substitution", "pt", _pt_subst_2),
    QuestionTemplate("subst_pt_3", "substitution", "pt", _pt_subst_3),
    QuestionTemplate("subst_pt_4", "substitution", "pt", _pt_subst_4),
    QuestionTemplate("subst_pt_5", "substitution", "pt", _pt_subst_5),
    QuestionTemplate("allergen_pt_1", "allergen", "pt", _pt_allergen_1),
    QuestionTemplate("allergen_pt_2", "allergen", "pt", _pt_allergen_2),
    QuestionTemplate("allergen_pt_3", "allergen", "pt", _pt_allergen_3),
    QuestionTemplate("allergen_pt_4", "allergen", "pt", _pt_allergen_4),
    QuestionTemplate("allergen_pt_5", "allergen", "pt", _pt_allergen_5),
    QuestionTemplate("reason_pt_1", "reasoning", "pt", _pt_reason_1),
    QuestionTemplate("reason_pt_2", "reasoning", "pt", _pt_reason_2),
    QuestionTemplate("reason_pt_3", "reasoning", "pt", _pt_reason_3),
    QuestionTemplate("reason_pt_4", "reasoning", "pt", _pt_reason_4),
    QuestionTemplate("reason_pt_5", "reasoning", "pt", _pt_reason_5),
    QuestionTemplate("reason_en_1", "reasoning", "en", _en_reason_1),
    QuestionTemplate("unknown_pt_1", "unknown_refusal", "pt", _pt_unknown_1),
    QuestionTemplate("unknown_pt_2", "unknown_refusal", "pt", _pt_unknown_2),
    QuestionTemplate("unknown_pt_3", "unknown_refusal", "pt", _pt_unknown_3),
    QuestionTemplate("unknown_pt_4", "unknown_refusal", "pt", _pt_unknown_4),
    QuestionTemplate("unknown_pt_5", "unknown_refusal", "pt", _pt_unknown_5),
    QuestionTemplate("unknown_en_1", "unknown_refusal", "en", _en_unknown_1),
    QuestionTemplate("household_pt_1", "household_portion", "pt", _pt_household_1),
    QuestionTemplate("household_pt_2", "household_portion", "pt", _pt_household_2),
    QuestionTemplate("household_pt_3", "household_portion", "pt", _pt_household_3),
    QuestionTemplate("household_pt_4", "household_portion", "pt", _pt_household_4),
    QuestionTemplate("household_pt_5", "household_portion", "pt", _pt_household_5),
]


def templates_for_category(category: str, language: str | None = None) -> list[QuestionTemplate]:
    items = [t for t in TEMPLATES if t.category == category]
    if language:
        items = [t for t in items if t.language == language]
    return items
