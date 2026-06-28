"""Build embedding text and RAG context strings from food records."""

from __future__ import annotations

from typing import Any

INGREDIENTS_MAX_LEN = 500


def _fmt_nutrient(label: str, value: float | None, unit: str) -> str | None:
    if value is None:
        return None
    return f"{label} {value:g}{unit}"


def build_embedding_text(record: dict[str, Any]) -> str:
    """Serialize a food record for dense embedding (Phase 3 template)."""
    parts: list[str] = []

    name = str(record.get("name") or "").strip()
    if name:
        parts.append(name)

    category = record.get("category")
    if category:
        parts.append(str(category))

    brand = record.get("brand")
    if brand:
        parts.append(str(brand))

    source = record.get("source")
    if source:
        parts.append(f"Source: {source}")

    serving_basis = record.get("serving_basis") or "100g"
    nutrients: list[str] = []
    for label, key, unit in (
        ("", "energy_kcal", " kcal"),
        ("protein", "protein_g", "g"),
        ("carbs", "carbohydrate_g", "g"),
        ("fat", "fat_g", "g"),
        ("fiber", "fiber_g", "g"),
        ("sodium", "sodium_mg", "mg"),
        ("sugar", "sugar_g", "g"),
    ):
        formatted = _fmt_nutrient(label, record.get(key), unit)
        if formatted:
            nutrients.append(formatted.strip())

    if nutrients:
        parts.append(f"Nutrients per {serving_basis}: " + ", ".join(nutrients))

    ingredients = record.get("ingredients_text")
    if ingredients:
        text = str(ingredients).strip()
        if len(text) > INGREDIENTS_MAX_LEN:
            text = text[: INGREDIENTS_MAX_LEN - 3] + "..."
        parts.append(f"Ingredients: {text}")

    return " | ".join(part for part in parts if part)


def build_rag_context(record: dict[str, Any]) -> str:
    """Short context block for LLM injection after retrieval."""
    source = record.get("source", "?")
    name = str(record.get("name") or "?")
    basis = record.get("serving_basis") or "100g"
    energy = record.get("energy_kcal")
    protein = record.get("protein_g")
    carbs = record.get("carbohydrate_g")
    fat = record.get("fat_g")

    macro_parts: list[str] = []
    if energy is not None:
        macro_parts.append(f"{energy:g} kcal")
    if protein is not None:
        macro_parts.append(f"P {protein:g}g")
    if carbs is not None:
        macro_parts.append(f"C {carbs:g}g")
    if fat is not None:
        macro_parts.append(f"G {fat:g}g")

    macros = ", ".join(macro_parts) if macro_parts else "macros unavailable"
    return f"[{source}] {name} ({basis}): {macros}"
