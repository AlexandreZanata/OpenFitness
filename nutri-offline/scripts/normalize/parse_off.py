#!/usr/bin/env python3
"""Parse Open Food Facts Parquet (Brazil filter) into FoodRecord rows."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import OFF_PARQUET, OFF_SOURCE_URL, PROCESSED_DIR

OUTPUT = PROCESSED_DIR / "off-brazil.parquet"

NUTRIENT_VALUE = """
    list_extract(list_filter(nutriments, x -> x.name = '{name}'), 1)."100g"
"""


def main() -> int:
    if not OFF_PARQUET.exists():
        raise SystemExit(f"Missing OFF parquet: {OFF_PARQUET}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(":memory:")
    parquet_path = OFF_PARQUET.as_posix()
    output_path = OUTPUT.as_posix()

    query = f"""
        SELECT
            'off:' || code AS id,
            'off' AS source,
            COALESCE(
                list_extract(product_name, 1).text,
                list_extract(product_name, 1).lang
            ) AS name,
            lower(regexp_replace(
                COALESCE(list_extract(product_name, 1).text, ''),
                '\\s+', ' ', 'g'
            )) AS name_normalized,
            'pt-BR' AS language,
            categories AS category,
            {NUTRIENT_VALUE.format(name="energy-kcal")} AS energy_kcal,
            {NUTRIENT_VALUE.format(name="proteins")} AS protein_g,
            {NUTRIENT_VALUE.format(name="carbohydrates")} AS carbohydrate_g,
            {NUTRIENT_VALUE.format(name="fat")} AS fat_g,
            {NUTRIENT_VALUE.format(name="fiber")} AS fiber_g,
            CASE
                WHEN {NUTRIENT_VALUE.format(name="sodium")} IS NOT NULL
                THEN {NUTRIENT_VALUE.format(name="sodium")} * 1000
            END AS sodium_mg,
            {NUTRIENT_VALUE.format(name="sugars")} AS sugar_g,
            CASE
                WHEN nutrition_data_per = '100ml' THEN '100ml'
                ELSE '100g'
            END AS serving_basis,
            list_extract(ingredients_text, 1).text AS ingredients_text,
            list_transform(allergens_tags, x -> regexp_replace(x, '^en:', '')) AS allergens,
            brands AS brand,
            code AS barcode,
            'BR' AS country,
            '{OFF_SOURCE_URL}' AS source_url,
            json_object(
                'code', code,
                'countries_tags', countries_tags,
                'nutriscore_grade', nutriscore_grade
            ) AS raw_metadata
        FROM read_parquet('{parquet_path}')
        WHERE list_contains(countries_tags, 'en:brazil')
          AND code IS NOT NULL
          AND len(product_name) > 0
    """

    count = connection.execute(f"SELECT count(*) FROM ({query})").fetchone()[0]
    connection.execute(f"COPY ({query}) TO '{output_path}' (FORMAT PARQUET)")
    print(f"OFF Brazil parsed: {count:,} rows -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
