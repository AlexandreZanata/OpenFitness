#!/usr/bin/env python3
"""Build food alias table from TACO/TBCA names + manual seeds (RAG-V2-07)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "normalize"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import FOOD_ALIASES_PARQUET, FOODS_PARQUET, PROCESSED_DIR  # noqa: E402
from schema import normalize_name  # noqa: E402

# Curated shorthand → canonical record (priority 0 beats mined aliases)
MANUAL_ALIAS_TARGETS: dict[str, str] = {
    "arroz": "taco:3",
    "banana": "taco:182",
    "feijao": "taco:561",
    "feijão": "taco:561",
    "carne": "taco:368",
    "frango": "taco:410",
    "ovo": "taco:488",
}

AUTHORITY_SOURCES = ("taco", "tbca")


def _head_term(name: str) -> str:
    return name.split(",")[0].strip()


def _mine_aliases(name: str) -> set[str]:
    """Generate searchable aliases from a canonical food name."""
    aliases: set[str] = set()
    normalized_full = normalize_name(name)
    if len(normalized_full) >= 3:
        aliases.add(normalized_full)

    head = _head_term(name)
    head_norm = normalize_name(head)
    if len(head_norm) >= 3:
        aliases.add(head_norm)

    tail = name.split(",", 1)[1].lower() if "," in name else ""
    descriptors = re.findall(r"\b(cozido|cozida|cru|crua|grelhado|grelhada|frito|frita)\b", tail)
    for descriptor in descriptors:
        candidate = normalize_name(f"{head} {descriptor}")
        if len(candidate) >= 3:
            aliases.add(candidate)

    if "tipo 1" in tail and head_norm:
        aliases.add(normalize_name(f"{head} tipo 1 cozido"))
        aliases.add(normalize_name(f"{head} branco cozido"))

    return aliases


def _fetch_records(connection: duckdb.DuckDBPyConnection) -> list[dict]:
    parquet = FOODS_PARQUET.as_posix()
    rows = connection.execute(
        f"""
        SELECT id, source, name, name_normalized
        FROM read_parquet('{parquet}')
        WHERE source IN ('taco', 'tbca')
        ORDER BY id
        """
    ).fetchall()
    return [
        {"id": row[0], "source": row[1], "name": row[2], "name_normalized": row[3]}
        for row in rows
    ]


def build_alias_rows(records: list[dict]) -> list[dict]:
    by_id = {record["id"]: record for record in records}
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add_row(*, alias: str, record_id: str, priority: int) -> None:
        alias_norm = normalize_name(alias)
        if len(alias_norm) < 3:
            return
        key = (alias_norm, record_id)
        if key in seen:
            return
        record = by_id.get(record_id)
        if record is None:
            return
        seen.add(key)
        rows.append(
            {
                "alias": alias_norm,
                "record_id": record_id,
                "canonical_name": record["name"],
                "source": record["source"],
                "priority": priority,
            }
        )

    for alias, record_id in MANUAL_ALIAS_TARGETS.items():
        add_row(alias=alias, record_id=record_id, priority=0)

    for record in records:
        for alias in _mine_aliases(record["name"]):
            add_row(alias=alias, record_id=record["id"], priority=1)

    rows.sort(key=lambda item: (item["alias"], item["priority"], item["record_id"]))
    return rows


def write_aliases(rows: list[dict], output: Path) -> int:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    table = pa.table(
        {
            "alias": [row["alias"] for row in rows],
            "record_id": [row["record_id"] for row in rows],
            "canonical_name": [row["canonical_name"] for row in rows],
            "source": [row["source"] for row in rows],
            "priority": [row["priority"] for row in rows],
        }
    )
    pq.write_table(table, output)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build NutriOffline food alias table")
    parser.add_argument(
        "--output",
        type=Path,
        default=FOOD_ALIASES_PARQUET,
        help="Output parquet path",
    )
    args = parser.parse_args()

    if not FOODS_PARQUET.exists():
        raise SystemExit(f"Missing {FOODS_PARQUET} — run Phase 2 first")

    connection = duckdb.connect(":memory:")
    records = _fetch_records(connection)
    rows = build_alias_rows(records)
    count = write_aliases(rows, args.output)

    manual = sum(1 for row in rows if row["priority"] == 0)
    print(
        f"PASS: food aliases built — {count:,} rows "
        f"({manual} manual seeds) -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
