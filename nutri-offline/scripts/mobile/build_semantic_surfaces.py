#!/usr/bin/env python3
"""Generate multi-surface semantic documents for mobile index (N-09-04)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mobile_paths import (  # noqa: E402
    FOOD_ALIASES_PARQUET,
    FOODS_PARQUET,
    INTENT_PROTOTYPES_JSON,
    LOG_DIR,
    MOBILE_EMBED_DIM,
    MOBILE_INDEX_DIR,
    MOBILE_RECORD_IDS_PARQUET,
    SEMANTIC_SURFACES_PARQUET,
)
from semantic_surfaces import (  # noqa: E402
    INTENT_PROTOTYPES,
    estimate_int8_vector_bytes,
    generate_surfaces_for_record,
    load_intent_prototypes,
)


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def load_mobile_records_with_aliases() -> list[dict]:
    connection = duckdb.connect(":memory:")
    foods = FOODS_PARQUET.as_posix()
    ids = MOBILE_RECORD_IDS_PARQUET.as_posix()
    rows = connection.execute(
        f"""
        SELECT
            f.id, f.source, f.name, f.name_normalized,
            f.category, f.brand, m.tier
        FROM read_parquet('{ids}') m
        JOIN read_parquet('{foods}') f ON m.id = f.id
        ORDER BY m.tier, f.id
        """
    ).fetchall()

    alias_map: dict[str, list[str]] = {}
    if FOOD_ALIASES_PARQUET.is_file():
        alias_rows = connection.execute(
            f"""
            SELECT a.record_id, a.alias
            FROM read_parquet('{FOOD_ALIASES_PARQUET.as_posix()}') a
            JOIN read_parquet('{ids}') m ON a.record_id = m.id
            """
        ).fetchall()
        for record_id, alias in alias_rows:
            alias_map.setdefault(str(record_id), []).append(str(alias))

    records: list[dict] = []
    for row in rows:
        record_id = str(row[0])
        records.append(
            {
                "id": record_id,
                "source": str(row[1]),
                "name": _text(row[2]),
                "name_normalized": _text(row[3]),
                "category": _text(row[4]),
                "brand": _text(row[5]),
                "tier": str(row[6]),
                "aliases": alias_map.get(record_id, []),
            }
        )
    return records


def build_surface_rows(records: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for record in records:
        surfaces = generate_surfaces_for_record(
            record_id=record["id"],
            name=record["name"],
            name_normalized=record["name_normalized"],
            category=record["category"],
            source=record["source"],
            brand=record["brand"],
            tier=record["tier"],
            aliases=record["aliases"],
        )
        for surface in surfaces:
            rows.append(
                {
                    "surface_id": surface.surface_id,
                    "record_id": surface.record_id,
                    "surface_kind": surface.surface_kind,
                    "search_text": surface.search_text,
                    "tier": record["tier"],
                    "source": record["source"],
                }
            )
    return rows


def write_surfaces_parquet(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE surfaces (
            surface_id VARCHAR,
            record_id VARCHAR,
            surface_kind VARCHAR,
            search_text VARCHAR,
            tier VARCHAR,
            source VARCHAR
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO surfaces VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["surface_id"],
                row["record_id"],
                row["surface_kind"],
                row["search_text"],
                row["tier"],
                row["source"],
            )
            for row in rows
        ],
    )
    connection.execute(f"COPY surfaces TO '{output_path.as_posix()}' (FORMAT PARQUET)")
    connection.close()


def summarize(rows: list[dict], *, records: list[dict]) -> dict:
    kind_counts = Counter(row["surface_kind"] for row in rows)
    tier_counts = Counter(row["tier"] for row in rows)
    source_counts = Counter(row["source"] for row in rows)
    int8_bytes = estimate_int8_vector_bytes(len(rows), dims=MOBILE_EMBED_DIM)
    taco_surfaces = sum(1 for row in rows if row["source"] == "taco")
    return {
        "record_count": len(records),
        "surface_count": len(rows),
        "taco_surface_count": taco_surfaces,
        "surfaces_by_kind": dict(kind_counts),
        "surfaces_by_tier": dict(tier_counts),
        "surfaces_by_source": dict(source_counts),
        "estimated_int8_bytes": int8_bytes,
        "intent_prototype_count": len(INTENT_PROTOTYPES),
        "within_vector_budget_90mb": int8_bytes <= 90 * 1024 * 1024,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build semantic surface documents for mobile pack")
    parser.add_argument("--record-id", help="Print surfaces for one record id")
    parser.add_argument("--output", type=Path, default=SEMANTIC_SURFACES_PARQUET)
    parser.add_argument("--stats-only", action="store_true", help="Skip parquet export")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if not MOBILE_RECORD_IDS_PARQUET.is_file():
        print("ERROR: run select_mobile_records.py first", file=sys.stderr)
        return 1

    records = load_mobile_records_with_aliases()
    if args.record_id:
        match = next((record for record in records if record["id"] == args.record_id), None)
        if match is None:
            print(f"ERROR: record not found: {args.record_id}", file=sys.stderr)
            return 1
        surfaces = generate_surfaces_for_record(
            record_id=match["id"],
            name=match["name"],
            name_normalized=match["name_normalized"],
            category=match["category"],
            source=match["source"],
            brand=match["brand"],
            tier=match["tier"],
            aliases=match["aliases"],
        )
        payload = [
            {
                "surface_id": surface.surface_id,
                "surface_kind": surface.surface_kind,
                "search_text": surface.search_text,
            }
            for surface in surfaces
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    rows = build_surface_rows(records)
    report = summarize(rows, records=records)

    if not args.stats_only:
        write_surfaces_parquet(rows, args.output)
        report["output"] = str(args.output)

    prototypes = load_intent_prototypes(INTENT_PROTOTYPES_JSON)
    report["intent_prototypes"] = len(prototypes)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "semantic-surfaces-build.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))

    if not report["within_vector_budget_90mb"]:
        print("WARN: estimated int8 size exceeds 90 MB vector budget", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
