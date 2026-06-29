"""Answer generation grounded in FoodRecord fields (Phase 4)."""

from __future__ import annotations

import math
from typing import Any

from constants import SOURCE_LABELS


def _is_valid_number(value: float | None) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return True


def source_label(source: str) -> str:
    return SOURCE_LABELS.get(source, source.upper())


def fmt_kcal(value: float | None) -> str | None:
    if not _is_valid_number(value):
        return None
    return str(int(round(value)))


def fmt_g(value: float | None) -> str | None:
    if not _is_valid_number(value):
        return None
    return f"{value:.1f}"


def scale_nutrient(value: float | None, portion_g: int, basis: str = "100g") -> float | None:
    if not _is_valid_number(value):
        return None
    if basis != "100g":
        return value
    return value * portion_g / 100.0


def macro_parts(record: dict[str, Any], portion_g: int = 100) -> list[str]:
    factor = portion_g / 100.0 if (record.get("serving_basis") or "100g") == "100g" else 1.0
    parts: list[str] = []
    energy = record.get("energy_kcal")
    if _is_valid_number(energy):
        parts.append(f"{fmt_kcal(energy * factor)} kcal")
    protein = record.get("protein_g")
    if _is_valid_number(protein):
        parts.append(f"{fmt_g(protein * factor)}g de proteína")
    carbs = record.get("carbohydrate_g")
    if _is_valid_number(carbs):
        parts.append(f"{fmt_g(carbs * factor)}g de carboidratos")
    fat = record.get("fat_g")
    if _is_valid_number(fat):
        parts.append(f"{fmt_g(fat * factor)}g de gordura")
    fiber = record.get("fiber_g")
    if _is_valid_number(fiber):
        parts.append(f"{fmt_g(fiber * factor)}g de fibras")
    return parts


def fmt_nutrient(nutrient_key: str, value: float) -> str:
    if nutrient_key == "energy_kcal":
        return f"{fmt_kcal(value)} kcal"
    return f"{fmt_g(value)}g"


def generate_direct_lookup(record: dict[str, Any], template_language: str) -> tuple[str, dict[str, Any]]:
    label = source_label(record["source"])
    name = record["name"]
    parts = macro_parts(record)
    if template_language == "en":
        macro_text = ", ".join(
            p.replace(" de proteína", " protein")
            .replace(" de carboidratos", " carbohydrates")
            .replace(" de gordura", " fat")
            .replace(" de fibras", " fiber")
            for p in parts
        )
        answer = (
            f"According to {label}, 100g of {name} contains approximately {macro_text}."
        )
    else:
        answer = (
            f"De acordo com a {label}, 100g de {name} contém aproximadamente "
            + ", ".join(parts)
            + "."
        )
    grounding = {
        "record_ids": [record["id"]],
        "values": {
            "energy_kcal": record.get("energy_kcal"),
            "protein_g": record.get("protein_g"),
            "carbohydrate_g": record.get("carbohydrate_g"),
            "fat_g": record.get("fat_g"),
        },
        "source_label": label,
    }
    return answer, grounding


def generate_portion_math(record: dict[str, Any], portion_g: int, template_language: str) -> tuple[str, dict[str, Any]]:
    label = source_label(record["source"])
    name = record["name"]
    parts = macro_parts(record, portion_g=portion_g)
    if template_language == "en":
        answer = (
            f"According to {label}, {portion_g}g of {name} provides approximately "
            + ", ".join(parts)
            + "."
        )
    else:
        answer = (
            f"Segundo a {label}, {portion_g}g de {name} fornecem aproximadamente "
            + ", ".join(parts)
            + "."
        )
    factor = portion_g / 100.0
    grounding = {
        "record_ids": [record["id"]],
        "portion_g": portion_g,
        "values": {
            "energy_kcal": None if record.get("energy_kcal") is None else record["energy_kcal"] * factor,
            "protein_g": None if record.get("protein_g") is None else record["protein_g"] * factor,
            "carbohydrate_g": None if record.get("carbohydrate_g") is None else record["carbohydrate_g"] * factor,
            "fat_g": None if record.get("fat_g") is None else record["fat_g"] * factor,
        },
        "source_label": label,
    }
    return answer, grounding


def generate_comparison(
    record_a: dict[str, Any],
    record_b: dict[str, Any],
    nutrient_key: str,
    nutrient_label_pt: str,
    template_language: str,
) -> tuple[str, dict[str, Any]]:
    label = source_label(record_a["source"])
    val_a = record_a.get(nutrient_key)
    val_b = record_b.get(nutrient_key)
    if val_a is None or val_b is None:
        raise ValueError("comparison requires both nutrient values")

    if val_a > val_b:
        winner, w_val, l_val = record_a["name"], val_a, val_b
    elif val_b > val_a:
        winner, w_val, l_val = record_b["name"], val_b, val_a
    else:
        winner, w_val, l_val = record_a["name"], val_a, val_b

    if template_language == "en":
        answer = (
            f"According to {label}, {record_a['name']} has {fmt_nutrient(nutrient_key, val_a)} "
            f"and {record_b['name']} has {fmt_nutrient(nutrient_key, val_b)} per 100g. "
            f"{winner} has more ({fmt_nutrient(nutrient_key, w_val)} vs {fmt_nutrient(nutrient_key, l_val)})."
        )
    else:
        nutrient_pt = "calorias" if nutrient_key == "energy_kcal" else nutrient_label_pt
        answer = (
            f"Segundo a {label}, {record_a['name']} tem {fmt_nutrient(nutrient_key, val_a)} de {nutrient_pt} "
            f"e {record_b['name']} tem {fmt_nutrient(nutrient_key, val_b)} por 100g. "
            f"{winner} tem mais ({fmt_nutrient(nutrient_key, w_val)} contra {fmt_nutrient(nutrient_key, l_val)})."
        )
    grounding = {
        "record_ids": [record_a["id"], record_b["id"]],
        "nutrient": nutrient_key,
        "values": {record_a["id"]: val_a, record_b["id"]: val_b},
        "source_label": label,
    }
    return answer, grounding


def generate_substitution(
    record: dict[str, Any],
    alt: dict[str, Any],
    template_language: str,
) -> tuple[str, dict[str, Any]]:
    label = source_label(record["source"])
    carbs_a = record.get("carbohydrate_g")
    carbs_b = alt.get("carbohydrate_g")
    if carbs_a is None or carbs_b is None or carbs_b >= carbs_a:
        raise ValueError("substitution requires lower-carb alternative")

    if template_language == "en":
        answer = (
            f"According to {label}, {alt['name']} ({fmt_g(carbs_b)}g carbs per 100g) "
            f"can replace {record['name']} ({fmt_g(carbs_a)}g carbs per 100g) for fewer carbohydrates."
        )
    else:
        answer = (
            f"Segundo a {label}, {alt['name']} ({fmt_g(carbs_b)}g de carboidratos por 100g) "
            f"pode substituir {record['name']} ({fmt_g(carbs_a)}g de carboidratos por 100g) "
            f"para reduzir carboidratos."
        )
    grounding = {
        "record_ids": [record["id"], alt["id"]],
        "values": {record["id"]: carbs_a, alt["id"]: carbs_b},
        "source_label": label,
    }
    return answer, grounding


def generate_allergen(record: dict[str, Any], allergen: str, contains: bool) -> tuple[str, dict[str, Any]]:
    label = source_label(record["source"])
    name = record["name"]
    if contains:
        answer = (
            f"De acordo com a {label}, {name} contém {allergen} "
            f"(informação declarada nos ingredientes ou alérgenos)."
        )
    else:
        answer = (
            f"De acordo com a {label}, {name} não declara {allergen} "
            f"nos ingredientes disponíveis — verifique o rótulo do produto."
        )
    grounding = {
        "record_ids": [record["id"]],
        "allergen": allergen,
        "contains": contains,
        "source_label": label,
    }
    return answer, grounding


def generate_reasoning(record: dict[str, Any], template_language: str) -> tuple[str, dict[str, Any]]:
    label = source_label(record["source"])
    name = record["name"]
    carbs = record.get("carbohydrate_g")
    protein = record.get("protein_g")
    energy = record.get("energy_kcal")
    fiber = record.get("fiber_g")

    if template_language == "en":
        answer = (
            f"Based on {label} data for {name}: approximately {fmt_kcal(energy)} kcal, "
            f"{fmt_g(protein)}g protein, {fmt_g(carbs)}g carbohydrates per 100g. "
            f"Higher carbohydrate content often correlates with higher glycemic impact; "
            f"this is an estimate — not a clinical glycemic index value."
        )
    else:
        fiber_note = ""
        if _is_valid_number(fiber):
            fiber_note = f" Com {fmt_g(fiber)}g de fibras por 100g, pode contribuir para saciedade."
        carb_protein = ""
        if carbs is not None and protein is not None:
            if carbs > protein:
                carb_protein = " É mais rico em carboidratos do que em proteína."
            elif protein > carbs:
                carb_protein = " É mais rico em proteína do que em carboidratos."
        answer = (
            f"Com base nos dados da {label} para {name}: aproximadamente {fmt_kcal(energy)} kcal, "
            f"{fmt_g(protein)}g de proteína e {fmt_g(carbs)}g de carboidratos por 100g."
            f"{carb_protein}{fiber_note} "
            f"Índice glicêmico exato não está na tabela — use como estimativa qualitativa."
        )
    grounding = {
        "record_ids": [record["id"]],
        "values": {
            "energy_kcal": energy,
            "protein_g": protein,
            "carbohydrate_g": carbs,
            "fiber_g": fiber,
        },
        "source_label": label,
    }
    return answer, grounding


def generate_unknown_refusal(food_name: str, template_language: str) -> tuple[str, dict[str, Any]]:
    if template_language == "en":
        answer = (
            f"I did not find {food_name} in TACO, USDA FoodData Central, or Open Food Facts. "
            f"I cannot provide nutritional values without a reliable source."
        )
    else:
        answer = (
            f"Não encontrei {food_name} na base de dados "
            f"(TACO, USDA FoodData Central ou Open Food Facts). "
            f"Não posso informar valores nutricionais sem uma fonte confiável."
        )
    grounding = {
        "record_ids": [],
        "refusal": True,
        "unknown_food": food_name,
        "source_label": "",
    }
    return answer, grounding


def generate_household_portion(
    record: dict[str, Any],
    *,
    portion_g: int,
    unit_label: str,
    template_language: str,
) -> tuple[str, dict[str, Any]]:
    label = source_label(record["source"])
    name = record["name"]
    parts = macro_parts(record, portion_g=portion_g)
    if template_language == "en":
        answer = (
            f"According to {label}, one {unit_label} of {name} ({portion_g}g) provides approximately "
            + ", ".join(parts)
            + "."
        )
    else:
        answer = (
            f"Segundo a {label}, {unit_label} de {name} ({portion_g}g) fornece aproximadamente "
            + ", ".join(parts)
            + "."
        )
    factor = portion_g / 100.0
    grounding = {
        "record_ids": [record["id"]],
        "portion_g": portion_g,
        "household_unit": unit_label,
        "values": {
            "energy_kcal": None if not _is_valid_number(record.get("energy_kcal")) else record["energy_kcal"] * factor,
            "protein_g": None if not _is_valid_number(record.get("protein_g")) else record["protein_g"] * factor,
            "carbohydrate_g": None
            if not _is_valid_number(record.get("carbohydrate_g"))
            else record["carbohydrate_g"] * factor,
            "fat_g": None if not _is_valid_number(record.get("fat_g")) else record["fat_g"] * factor,
        },
        "source_label": label,
    }
    return answer, grounding
