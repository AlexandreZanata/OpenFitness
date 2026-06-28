#!/usr/bin/env python3
"""Merge per-source parquets into unified foods.parquet."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import FOODS_PARQUET, PROCESSED_DIR, SOURCE_COUNTS_JSON

SOURCE_FILES = {
    "taco": PROCESSED_DIR / "taco.parquet",
    "fdc": PROCESSED_DIR / "fdc.parquet",
    "off": PROCESSED_DIR / "off-brazil.parquet",
}


def main() -> int:
    missing = [name for name, path in SOURCE_FILES.items() if not path.exists()]
    if missing:
        raise SystemExit(f"Missing source parquets: {missing}")

    FOODS_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(":memory:")

    union_parts = [
        f"SELECT *, '{source}' AS _source FROM read_parquet('{path.as_posix()}')"
        for source, path in SOURCE_FILES.items()
    ]
    connection.execute(
        f"""
        CREATE TABLE foods AS
        SELECT * EXCLUDE (_source)
        FROM ({" UNION ALL ".join(union_parts)})
        """
    )

    duplicates = connection.execute(
        """
        SELECT id, count(*) AS n
        FROM foods
        GROUP BY id
        HAVING count(*) > 1
        ORDER BY n DESC
        LIMIT 20
        """
    ).fetchdf()
    if not duplicates.empty:
        dup_path = PROCESSED_DIR / "duplicate_ids.log"
        duplicates.to_csv(dup_path, index=False)
        raise SystemExit(f"FAIL: duplicate ids found — logged to {dup_path}")

    connection.execute(f"COPY foods TO '{FOODS_PARQUET.as_posix()}' (FORMAT PARQUET)")

    counts = connection.execute(
        "SELECT source, count(*) AS rows FROM foods GROUP BY source ORDER BY source"
    ).fetchdf()
    source_counts = {row["source"]: int(row["rows"]) for _, row in counts.iterrows()}
    SOURCE_COUNTS_JSON.write_text(
        json.dumps({"sources": source_counts, "total": sum(source_counts.values())}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    print(f"Merged {source_counts} -> {FOODS_PARQUET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
