#!/usr/bin/env python3
"""Build DuckDB materialized database from foods.parquet."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import FOODS_DUCKDB, FOODS_PARQUET


def main() -> int:
    if not FOODS_PARQUET.exists():
        raise SystemExit(f"Missing {FOODS_PARQUET} — run merge.py first")

    if FOODS_DUCKDB.exists():
        FOODS_DUCKDB.unlink()

    connection = duckdb.connect(str(FOODS_DUCKDB))
    connection.execute(
        f"""
        CREATE TABLE foods AS
        SELECT * FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        """
    )
    connection.execute("CREATE INDEX idx_foods_source ON foods(source)")
    connection.execute("CREATE INDEX idx_foods_name_normalized ON foods(name_normalized)")

    count = connection.execute("SELECT count(*) FROM foods").fetchone()[0]
    connection.close()
    print(f"DuckDB materialized: {count:,} rows -> {FOODS_DUCKDB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
