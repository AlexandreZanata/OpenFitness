"""FoodRecord unified schema for NutriOffline (Phase 2)."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

FoodSource = Literal["taco", "tbca", "fdc", "off"]
ServingBasis = Literal["100g", "100ml", "serving"]


def normalize_name(name: str) -> str:
    """Lowercase, strip accents, collapse whitespace for dedup/search."""
    if not name:
        return ""
    normalized = unicodedata.normalize("NFKD", name)
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    collapsed = re.sub(r"\s+", " ", without_accents.lower().strip())
    return collapsed


def make_id(source: FoodSource, native_id: str) -> str:
    return f"{source}:{native_id}"


class FoodRecord(BaseModel):
    id: str
    source: FoodSource
    name: str
    name_normalized: str
    language: str
    category: str | None = None
    energy_kcal: float | None = None
    protein_g: float | None = None
    carbohydrate_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None
    sugar_g: float | None = None
    serving_basis: ServingBasis = "100g"
    ingredients_text: str | None = None
    allergens: list[str] = Field(default_factory=list)
    brand: str | None = None
    barcode: str | None = None
    country: str | None = None
    source_url: str
    raw_metadata: dict[str, Any] | None = None

    @field_validator("energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "fiber_g", "sodium_mg", "sugar_g")
    @classmethod
    def non_negative_nutrients(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("nutrient values must be >= 0 when present")
        return value

    @classmethod
    def build(
        cls,
        *,
        source: FoodSource,
        native_id: str,
        name: str,
        language: str,
        source_url: str,
        serving_basis: ServingBasis = "100g",
        category: str | None = None,
        energy_kcal: float | None = None,
        protein_g: float | None = None,
        carbohydrate_g: float | None = None,
        fat_g: float | None = None,
        fiber_g: float | None = None,
        sodium_mg: float | None = None,
        sugar_g: float | None = None,
        ingredients_text: str | None = None,
        allergens: list[str] | None = None,
        brand: str | None = None,
        barcode: str | None = None,
        country: str | None = None,
        raw_metadata: dict[str, Any] | None = None,
    ) -> FoodRecord:
        return cls(
            id=make_id(source, native_id),
            source=source,
            name=name.strip(),
            name_normalized=normalize_name(name),
            language=language,
            category=category,
            energy_kcal=energy_kcal,
            protein_g=protein_g,
            carbohydrate_g=carbohydrate_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
            sodium_mg=sodium_mg,
            sugar_g=sugar_g,
            serving_basis=serving_basis,
            ingredients_text=ingredients_text,
            allergens=allergens or [],
            brand=brand,
            barcode=barcode,
            country=country,
            source_url=source_url,
            raw_metadata=raw_metadata,
        )

    def to_row(self) -> dict[str, Any]:
        row = self.model_dump()
        row["allergens"] = list(self.allergens)
        if self.raw_metadata is not None:
            row["raw_metadata"] = json.dumps(self.raw_metadata, ensure_ascii=False)
        else:
            row["raw_metadata"] = None
        return row
