#!/usr/bin/env python3
"""Phase 2 validation — golden rows and BR-NORM rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import FOODS_DUCKDB, FOODS_PARQUET, PROCESSED_DIR, STATS_JSON, TACO_OFFICIAL_XLSX

LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "validate-normalization.log"
TOLERANCE_PCT = 1.0

# Official TACO 4th ed values (from taco-oficial.xlsx, CMVCol taco3)
GOLDEN_TACO = [
    {
        "id": "BR-NORM-001a",
        "name_contains": "tipo 1, cozido",
        "field": "energy_kcal",
        "expected": 128.25848566666664,
        "note": "Arroz branco cozido equivalent (TACO: Arroz, tipo 1, cozido)",
    },
    {
        "id": "BR-NORM-001b",
        "name_contains": "tipo 1, cozido",
        "field": "carbohydrate_g",
        "expected": 28.059849999999994,
    },
    {
        "id": "BR-NORM-001c",
        "name_contains": "banana, prata, crua",
        "field": "energy_kcal",
        "expected": 98.24970217391306,
    },
]

NUTRIENT_FIELDS = [
    "energy_kcal",
    "protein_g",
    "carbohydrate_g",
    "fat_g",
    "fiber_g",
    "sodium_mg",
    "sugar_g",
]


def log(message: str) -> None:
    print(message, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def within_tolerance(actual: float, expected: float, tolerance_pct: float) -> bool:
    if expected == 0:
        return abs(actual - expected) <= 0.01
    return abs(actual - expected) / abs(expected) * 100 <= tolerance_pct


def check_golden_taco(connection: duckdb.DuckDBPyConnection) -> None:
    for case in GOLDEN_TACO:
        field = case["field"]
        row = connection.execute(
            f"""
            SELECT name, {field} AS value
            FROM read_parquet('{FOODS_PARQUET.as_posix()}')
            WHERE source = 'taco'
              AND lower(name) LIKE ?
            LIMIT 1
            """,
            [f"%{case['name_contains'].lower()}%"],
        ).fetchone()
        if row is None or row[1] is None:
            raise SystemExit(f"FAIL {case['id']}: no TACO row for '{case['name_contains']}'")
        actual = float(row[1])
        expected = float(case["expected"])
        if not within_tolerance(actual, expected, TOLERANCE_PCT):
            raise SystemExit(
                f"FAIL {case['id']}: {row[0]} {field}={actual} expected {expected} (±{TOLERANCE_PCT}%)"
            )
        log(f"PASS {case['id']}: {row[0]} {field}={actual:.2f} (expected {expected:.2f})")


def check_br_norm_rules(connection: duckdb.DuckDBPyConnection) -> None:
    negative_energy = connection.execute(
        f"""
        SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE energy_kcal IS NOT NULL AND energy_kcal < 0
        """
    ).fetchone()[0]
    if negative_energy:
        raise SystemExit(f"FAIL BR-NORM-002: {negative_energy} rows with negative energy_kcal")

    dup_ids = connection.execute(
        f"""
        SELECT count(*) FROM (
            SELECT id FROM read_parquet('{FOODS_PARQUET.as_posix()}')
            GROUP BY id HAVING count(*) > 1
        )
        """
    ).fetchone()[0]
    if dup_ids:
        raise SystemExit(f"FAIL BR-NORM-003: {dup_ids} duplicate ids")

    off_brazil = connection.execute(
        f"""
        SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE source = 'off'
        """
    ).fetchone()[0]
    if off_brazil <= 0:
        raise SystemExit("FAIL BR-NORM-004: OFF Brazil subset is empty")
    log(f"PASS BR-NORM-004: OFF Brazil rows = {off_brazil:,}")


def check_row_counts(connection: duckdb.DuckDBPyConnection) -> None:
    taco_count = connection.execute(
        f"SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}') WHERE source = 'taco'"
    ).fetchone()[0]
    if not (500 <= taco_count <= 700):
        raise SystemExit(f"FAIL: TACO row count {taco_count} outside 500–700")

    total = connection.execute(
        f"SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}')"
    ).fetchone()[0]
    if total < 100_000:
        raise SystemExit(f"FAIL: foods.parquet total {total} < 100k")
    log(f"PASS row counts: taco={taco_count}, total={total:,}")


def build_stats(connection: duckdb.DuckDBPyConnection) -> dict:
    total = connection.execute(f"SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}')").fetchone()[0]
    by_source = connection.execute(
        f"""
        SELECT source, count(*) AS rows
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        GROUP BY source ORDER BY source
        """
    ).fetchdf()

    completeness = connection.execute(
        f"""
        SELECT
            source,
            round(100.0 * count(energy_kcal) / count(*), 2) AS energy_kcal_pct,
            round(100.0 * count(protein_g) / count(*), 2) AS protein_g_pct,
            round(100.0 * count(carbohydrate_g) / count(*), 2) AS carbohydrate_g_pct,
            round(100.0 * count(fat_g) / count(*), 2) AS fat_g_pct
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        GROUP BY source
        """
    ).fetchdf()

    top_categories = connection.execute(
        f"""
        SELECT category, count(*) AS rows
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY rows DESC
        LIMIT 20
        """
    ).fetchdf()

    energy_no_macros = connection.execute(
        f"""
        SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE energy_kcal IS NOT NULL
          AND protein_g IS NULL AND carbohydrate_g IS NULL AND fat_g IS NULL
        """
    ).fetchone()[0]

    stats = {
        "total_rows": int(total),
        "rows_by_source": {row["source"]: int(row["rows"]) for _, row in by_source.iterrows()},
        "field_completeness_pct": completeness.to_dict(orient="records"),
        "top_categories": top_categories.to_dict(orient="records"),
        "energy_without_macros": int(energy_no_macros),
        "golden_taco_reference": "values from taco-oficial.xlsx CMVCol taco3",
    }
    STATS_JSON.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return stats


def manual_taco_spot_check() -> None:
    """Compare 5 random TACO rows against official Excel (manual review aid)."""
    sample = pd.read_parquet(PROCESSED_DIR / "taco.parquet").sample(5, random_state=42)
    official = pd.read_excel(TACO_OFFICIAL_XLSX, sheet_name="CMVCol taco3", header=None)
    log("Manual spot-check sample (compare with official Excel):")
    for _, row in sample.iterrows():
        num = row["raw_metadata"]
        if isinstance(num, str):
            import json as _json

            num = _json.loads(num).get("taco_number")
        log(f"  - {row['name']} energy_kcal={row.get('energy_kcal')}")


def main() -> int:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    if not FOODS_PARQUET.exists():
        raise SystemExit(f"Missing {FOODS_PARQUET}")

    log("NutriOffline Phase 2 validation")
    connection = duckdb.connect(":memory:")
    check_golden_taco(connection)
    check_br_norm_rules(connection)
    check_row_counts(connection)
    stats = build_stats(connection)
    manual_taco_spot_check()

    if FOODS_DUCKDB.exists():
        sample = connection.execute(
            f"""
            SELECT name, source, energy_kcal
            FROM read_parquet('{FOODS_PARQUET.as_posix()}')
            WHERE name_normalized LIKE '%arroz%'
            LIMIT 3
            """
        ).fetchdf()
        log(f"DuckDB sample search 'arroz': {sample.to_dict(orient='records')}")

    log(f"Stats written to {STATS_JSON} (total={stats['total_rows']:,})")
    log("PASS: Phase 2 validation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
