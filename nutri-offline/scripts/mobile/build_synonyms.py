#!/usr/bin/env python3
"""Build compact synonym sqlite for mobile pack (N-09-02)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "normalize"))

from mobile_paths import (  # noqa: E402
    FOOD_ALIASES_PARQUET,
    LOG_DIR,
    MOBILE_INDEX_DIR,
    MOBILE_RECORD_IDS_PARQUET,
    SYNONYMS_DB,
)
from mobile_sqlite import connect  # noqa: E402
from synonym_resolver import normalize_phrase_key  # noqa: E402

MANUAL_SYNONYMS_JSON = Path(__file__).resolve().parents[2] / "config" / "semantic" / "manual_synonyms.json"


def load_manual_entries(path: Path = MANUAL_SYNONYMS_JSON) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["entries"]


def _fetch_alias_rows(
    *,
    aliases_parquet: Path,
    mobile_ids_parquet: Path,
) -> list[tuple[str, str, str, str, int]]:
    if not aliases_parquet.is_file() or not mobile_ids_parquet.is_file():
        return []
    duck = duckdb.connect(":memory:")
    return duck.execute(
        f"""
        SELECT a.alias, a.record_id, a.canonical_name, a.source, a.priority
        FROM read_parquet('{aliases_parquet.as_posix()}') a
        JOIN read_parquet('{mobile_ids_parquet.as_posix()}') m
          ON a.record_id = m.id
        ORDER BY a.alias, a.priority, a.record_id
        """
    ).fetchall()


def build_synonyms_db(
    *,
    entries: list[dict],
    output_path: Path,
    alias_rows: list[tuple[str, str, str, str, int]],
) -> dict:
    if output_path.exists():
        output_path.unlink()

    connection = connect(str(output_path))
    connection.execute(
        """
        CREATE TABLE synonym_map (
            phrase TEXT NOT NULL,
            record_id TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            source TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            label TEXT,
            is_default INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (phrase, record_id)
        )
        """
    )
    connection.execute("CREATE INDEX idx_synonym_phrase ON synonym_map(phrase)")

    manual_rows = 0
    seen: set[tuple[str, str]] = set()

    def insert_row(
        *,
        phrase: str,
        record_id: str,
        canonical_name: str,
        source: str,
        priority: int,
        label: str | None,
        is_default: bool,
    ) -> None:
        key = normalize_phrase_key(phrase)
        dedupe = (key, record_id)
        if not key or dedupe in seen:
            return
        seen.add(dedupe)
        connection.execute(
            """
            INSERT OR IGNORE INTO synonym_map(
                phrase, record_id, canonical_name, source, priority, label, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (key, record_id, canonical_name, source, priority, label, int(is_default)),
        )

    for entry in entries:
        phrase = entry["phrase"]
        default_id = entry["default_record_id"]
        label = entry.get("label")
        for index, record_id in enumerate(entry["candidates"]):
            insert_row(
                phrase=phrase,
                record_id=record_id,
                canonical_name=record_id,
                source="manual",
                priority=index,
                label=label,
                is_default=record_id == default_id,
            )
            manual_rows += 1

    alias_rows_written = 0
    for alias, record_id, canonical_name, source, priority in alias_rows:
        before = len(seen)
        insert_row(
            phrase=alias,
            record_id=record_id,
            canonical_name=canonical_name,
            source=source,
            priority=priority + 10,
            label=None,
            is_default=False,
        )
        if len(seen) > before:
            alias_rows_written += 1

    connection.commit()
    total = connection.execute("SELECT COUNT(*) FROM synonym_map").fetchone()[0]
    size_bytes = output_path.stat().st_size
    connection.close()
    return {
        "manual_rows": manual_rows,
        "alias_rows": alias_rows_written,
        "total_rows": int(total),
        "size_bytes": size_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build mobile synonym sqlite")
    parser.add_argument("--manual", type=Path, default=MANUAL_SYNONYMS_JSON)
    parser.add_argument("--output", type=Path, default=SYNONYMS_DB)
    args = parser.parse_args()

    if not args.manual.is_file():
        print(f"ERROR: missing manual synonyms: {args.manual}", file=sys.stderr)
        return 1

    MOBILE_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    entries = load_manual_entries(args.manual)
    alias_rows = _fetch_alias_rows(
        aliases_parquet=FOOD_ALIASES_PARQUET,
        mobile_ids_parquet=MOBILE_RECORD_IDS_PARQUET,
    )
    summary = build_synonyms_db(entries=entries, output_path=args.output, alias_rows=alias_rows)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "mobile-synonyms-build.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    limit = 8 * 1024 * 1024
    if summary["size_bytes"] > limit:
        print(
            f"WARN: synonyms.db {summary['size_bytes']} bytes exceeds 8 MB budget",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
