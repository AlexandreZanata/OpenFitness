#!/usr/bin/env python3
"""Build compact FTS5 lexicon + alias sqlite for mobile pack (N-08-07)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mobile_paths import FOOD_ALIASES_PARQUET, LOG_DIR, MOBILE_INDEX_DIR, MOBILE_RECORD_IDS_PARQUET, VECTORS_DB, LEXICON_DB, INTENT_PROTOTYPES_JSON  # noqa: E402
from mobile_sqlite import connect  # noqa: E402
from semantic_surfaces import load_intent_prototypes  # noqa: E402


def build_lexicon(
    *,
    vectors_db: Path,
    aliases_parquet: Path,
    mobile_ids_parquet: Path,
    output_path: Path,
) -> dict:
    if output_path.exists():
        output_path.unlink()

    source = connect(str(vectors_db), readonly=True)
    rows = source.execute(
        "SELECT id, search_text, source, name FROM food_meta ORDER BY rowid"
    ).fetchall()
    source.close()

    connection = connect(str(output_path))
    connection.execute(
        """
        CREATE VIRTUAL TABLE food_fts USING fts5(
            record_id UNINDEXED,
            source UNINDEXED,
            name,
            search_text,
            tokenize='unicode61 remove_diacritics 2'
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE aliases (
            alias TEXT NOT NULL,
            record_id TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            source TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (alias, record_id)
        )
        """
    )
    connection.executemany(
        "INSERT INTO food_fts(record_id, source, name, search_text) VALUES (?, ?, ?, ?)",
        rows,
    )

    alias_count = 0
    if aliases_parquet.is_file() and mobile_ids_parquet.is_file():
        duck = duckdb.connect(":memory:")
        alias_rows = duck.execute(
            f"""
            SELECT a.alias, a.record_id, a.canonical_name, a.source, a.priority
            FROM read_parquet('{aliases_parquet.as_posix()}') a
            JOIN read_parquet('{mobile_ids_parquet.as_posix()}') m
              ON a.record_id = m.id
            ORDER BY a.alias, a.priority, a.record_id
            """
        ).fetchall()
        connection.executemany(
            """
            INSERT OR IGNORE INTO aliases(alias, record_id, canonical_name, source, priority)
            VALUES (?, ?, ?, ?, ?)
            """,
            alias_rows,
        )
        alias_count = len(alias_rows)

    intent_count = 0
    if INTENT_PROTOTYPES_JSON.is_file():
        connection.execute(
            """
            CREATE TABLE intent_prototypes (
                id TEXT PRIMARY KEY,
                intent_kind TEXT NOT NULL,
                regex TEXT NOT NULL,
                search_text TEXT NOT NULL
            )
            """
        )
        prototypes = load_intent_prototypes(INTENT_PROTOTYPES_JSON)
        connection.executemany(
            """
            INSERT INTO intent_prototypes(id, intent_kind, regex, search_text)
            VALUES (?, ?, ?, ?)
            """,
            [
                (item["id"], item["intent_kind"], item["regex"], item["search_text"])
                for item in prototypes
            ],
        )
        intent_count = len(prototypes)

    connection.commit()
    size_bytes = output_path.stat().st_size
    connection.close()
    return {
        "alias_rows": alias_count,
        "fts_rows": len(rows),
        "intent_prototype_rows": intent_count,
        "size_bytes": size_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build mobile lexicon sqlite")
    parser.add_argument("--vectors-db", type=Path, default=VECTORS_DB)
    parser.add_argument("--output", type=Path, default=LEXICON_DB)
    args = parser.parse_args()

    if not args.vectors_db.is_file():
        print("ERROR: vectors.db missing — run build_mobile_index.py first", file=sys.stderr)
        return 1

    MOBILE_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    summary = build_lexicon(
        vectors_db=args.vectors_db,
        aliases_parquet=FOOD_ALIASES_PARQUET,
        mobile_ids_parquet=MOBILE_RECORD_IDS_PARQUET,
        output_path=args.output,
    )
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "mobile-lexicon-build.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    limit = 8 * 1024 * 1024
    if summary["size_bytes"] > limit:
        print(
            f"WARN: lexicon {summary['size_bytes']} bytes exceeds 8 MB budget",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
