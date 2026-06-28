"""Load and sample food records from foods.parquet."""

from __future__ import annotations

from typing import Any

import duckdb

from _paths import FOODS_PARQUET, FDC_FOUNDATION_SQL


def connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect()


def fetch_records(
    connection: duckdb.DuckDBPyConnection,
    sql_where: str,
    *,
    limit: int | None = None,
    require_energy: bool = True,
) -> list[dict[str, Any]]:
    energy_clause = "AND energy_kcal IS NOT NULL" if require_energy else ""
    limit_clause = f"LIMIT {limit}" if limit else ""
    rows = connection.execute(
        f"""
        SELECT *
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE {sql_where}
          {energy_clause}
        ORDER BY id
        {limit_clause}
        """
    ).fetchdf()
    return rows.to_dict(orient="records")


def fetch_taco(connection: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    return fetch_records(connection, "source = 'taco'")


def fetch_fdc_foundation(connection: duckdb.DuckDBPyConnection, limit: int = 800) -> list[dict[str, Any]]:
    return fetch_records(connection, FDC_FOUNDATION_SQL.strip(), limit=limit)


def fetch_off_brazil(connection: duckdb.DuckDBPyConnection, limit: int = 1500) -> list[dict[str, Any]]:
    return fetch_records(
        connection,
        "source = 'off' AND upper(country) = 'BR'",
        limit=limit,
    )


def fetch_off_with_ingredients(connection: duckdb.DuckDBPyConnection, limit: int = 800) -> list[dict[str, Any]]:
    return fetch_records(
        connection,
        """
        source = 'off'
        AND upper(country) = 'BR'
        AND ingredients_text IS NOT NULL
        AND length(trim(ingredients_text)) > 20
        """,
        limit=limit,
        require_energy=False,
    )


def fetch_comparison_pairs(
    connection: duckdb.DuckDBPyConnection,
    source: str,
    limit: int = 500,
) -> list[tuple[dict[str, Any], dict[str, Any], str]]:
    """Return (record_a, record_b, nutrient_key) tuples grouped by category."""
    rows = connection.execute(
        f"""
        SELECT id, name, source, category, energy_kcal, protein_g, carbohydrate_g, fat_g,
               fiber_g, serving_basis, ingredients_text, allergens, brand, country, source_url
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE source = ?
          AND category IS NOT NULL
          AND energy_kcal IS NOT NULL
          AND protein_g IS NOT NULL
          AND carbohydrate_g IS NOT NULL
        ORDER BY category, id
        """,
        [source],
    ).fetchdf()

    pairs: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    nutrients = ["protein_g", "carbohydrate_g", "fat_g", "energy_kcal"]
    by_category: dict[str, list[dict[str, Any]]] = {}
    for record in rows.to_dict(orient="records"):
        category = record["category"] or "unknown"
        by_category.setdefault(category, []).append(record)

    for items in by_category.values():
        if len(items) < 2:
            continue
        for index in range(0, len(items) - 1, 2):
            if len(pairs) >= limit:
                return pairs
            record_a = items[index]
            record_b = items[index + 1]
            nutrient = nutrients[len(pairs) % len(nutrients)]
            pairs.append((record_a, record_b, nutrient))
    return pairs


def fetch_substitution_pairs(
    connection: duckdb.DuckDBPyConnection,
    source: str,
    limit: int = 400,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    rows = connection.execute(
        f"""
        SELECT id, name, source, category, carbohydrate_g, energy_kcal, protein_g, fat_g,
               serving_basis, ingredients_text, source_url
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE source = ?
          AND category IS NOT NULL
          AND carbohydrate_g IS NOT NULL
        ORDER BY category, carbohydrate_g DESC
        """,
        [source],
    ).fetchdf()

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    by_category: dict[str, list[dict[str, Any]]] = {}
    for record in rows.to_dict(orient="records"):
        category = record["category"] or "unknown"
        by_category.setdefault(category, []).append(record)

    for items in by_category.values():
        if len(items) < 2:
            continue
        high = items[0]
        for low in reversed(items):
            if low["id"] == high["id"]:
                continue
            if low["carbohydrate_g"] < high["carbohydrate_g"]:
                pairs.append((high, low))
                break
            if len(pairs) >= limit:
                return pairs
    return pairs[:limit]
