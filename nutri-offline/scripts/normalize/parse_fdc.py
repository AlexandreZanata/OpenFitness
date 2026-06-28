#!/usr/bin/env python3
"""Parse USDA FoodData Central bulk CSV into FoodRecord rows."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import (
    FDC_BRANDED_DIR,
    FDC_FOUNDATION_DIR,
    FDC_SOURCE_URL,
    NUTRIENT_IDS,
    PROCESSED_DIR,
)

OUTPUT = PROCESSED_DIR / "fdc.parquet"

NUTRIENT_CASES = ",\n".join(
    f"MAX(CASE WHEN fn.nutrient_id = {nutrient_id} THEN fn.amount END) AS {field}"
    for field, nutrient_id in NUTRIENT_IDS.items()
)
NUTRIENT_ID_LIST = ", ".join(str(value) for value in NUTRIENT_IDS.values())


def _foundation_query(dataset_dir: Path) -> str:
    food_csv = (dataset_dir / "food.csv").as_posix()
    nutrient_csv = (dataset_dir / "food_nutrient.csv").as_posix()
    category_csv = (dataset_dir / "food_category.csv").as_posix()
    return f"""
        SELECT
            'fdc:' || CAST(f.fdc_id AS VARCHAR) AS id,
            'fdc' AS source,
            f.description AS name,
            lower(regexp_replace(f.description, '\\s+', ' ', 'g')) AS name_normalized,
            'en' AS language,
            fc.description AS category,
            nutrients.energy_kcal,
            nutrients.protein_g,
            nutrients.carbohydrate_g,
            nutrients.fat_g,
            nutrients.fiber_g,
            nutrients.sodium_mg,
            nutrients.sugar_g,
            '100g' AS serving_basis,
            NULL AS ingredients_text,
            []::VARCHAR[] AS allergens,
            NULL AS brand,
            NULL AS barcode,
            'US' AS country,
            '{FDC_SOURCE_URL}' AS source_url,
            json_object('fdc_id', f.fdc_id, 'data_type', f.data_type, 'dataset', 'foundation') AS raw_metadata
        FROM read_csv('{food_csv}') f
        LEFT JOIN read_csv('{category_csv}') fc ON fc.id = f.food_category_id
        LEFT JOIN (
            SELECT fn.fdc_id, {NUTRIENT_CASES}
            FROM read_csv('{nutrient_csv}') fn
            WHERE fn.nutrient_id IN ({NUTRIENT_ID_LIST})
            GROUP BY fn.fdc_id
        ) nutrients ON nutrients.fdc_id = f.fdc_id
    """


def _branded_query(dataset_dir: Path) -> str:
    food_csv = (dataset_dir / "food.csv").as_posix()
    nutrient_csv = (dataset_dir / "food_nutrient.csv").as_posix()
    branded_csv = (dataset_dir / "branded_food.csv").as_posix()
    return f"""
        SELECT
            'fdc:' || CAST(f.fdc_id AS VARCHAR) AS id,
            'fdc' AS source,
            f.description AS name,
            lower(regexp_replace(f.description, '\\s+', ' ', 'g')) AS name_normalized,
            'en' AS language,
            bf.branded_food_category AS category,
            nutrients.energy_kcal,
            nutrients.protein_g,
            nutrients.carbohydrate_g,
            nutrients.fat_g,
            nutrients.fiber_g,
            nutrients.sodium_mg,
            nutrients.sugar_g,
            '100g' AS serving_basis,
            bf.ingredients AS ingredients_text,
            []::VARCHAR[] AS allergens,
            COALESCE(bf.brand_name, bf.brand_owner) AS brand,
            bf.gtin_upc AS barcode,
            COALESCE(bf.market_country, 'US') AS country,
            '{FDC_SOURCE_URL}' AS source_url,
            json_object('fdc_id', f.fdc_id, 'data_type', f.data_type, 'dataset', 'branded') AS raw_metadata
        FROM read_csv('{food_csv}') f
        LEFT JOIN read_csv('{branded_csv}') bf ON bf.fdc_id = f.fdc_id
        LEFT JOIN (
            SELECT fn.fdc_id, {NUTRIENT_CASES}
            FROM read_csv('{nutrient_csv}') fn
            WHERE fn.nutrient_id IN ({NUTRIENT_ID_LIST})
            GROUP BY fn.fdc_id
        ) nutrients ON nutrients.fdc_id = f.fdc_id
    """


def main() -> int:
    if not FDC_FOUNDATION_DIR.exists() or not FDC_BRANDED_DIR.exists():
        raise SystemExit("Missing FDC extracted directories — run Phase 1 downloads first")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(":memory:")

    foundation_query = _foundation_query(FDC_FOUNDATION_DIR)
    branded_query = _branded_query(FDC_BRANDED_DIR)
    foundation_count = connection.execute(f"SELECT count(*) FROM ({foundation_query})").fetchone()[0]
    branded_count = connection.execute(f"SELECT count(*) FROM ({branded_query})").fetchone()[0]

    connection.execute(
        f"""
        COPY (
            {foundation_query}
            UNION ALL
            {branded_query}
        ) TO '{OUTPUT.as_posix()}' (FORMAT PARQUET)
        """
    )

    total = int(foundation_count) + int(branded_count)
    print(
        f"FDC parsed: foundation={foundation_count}, branded={branded_count}, total={total} -> {OUTPUT}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
