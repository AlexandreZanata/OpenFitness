"""Full-catalog index helpers — Phase 11 (N-11)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from _paths import FOODS_PARQUET, INDEX_DIR, INDEX_METADATA, TABLE_NAME
from build_index import scope_sql


@dataclass(frozen=True)
class CatalogSnapshot:
    scope: str
    total_rows: int
    source_counts: dict[str, int]


@dataclass(frozen=True)
class IndexSnapshot:
    scope: str
    record_count: int
    source_counts: dict[str, int]
    index_size_mb: float | None
    schema_version: int


def load_index_metadata() -> dict[str, Any]:
    if not INDEX_METADATA.is_file():
        return {}
    return json.loads(INDEX_METADATA.read_text(encoding="utf-8"))


def index_snapshot() -> IndexSnapshot | None:
    meta = load_index_metadata()
    if not meta:
        return None
    return IndexSnapshot(
        scope=str(meta.get("scope", "v1")),
        record_count=int(meta.get("record_count", 0)),
        source_counts={str(k): int(v) for k, v in (meta.get("source_counts") or {}).items()},
        index_size_mb=meta.get("index_size_mb"),
        schema_version=int(meta.get("schema_version", 1)),
    )


def parquet_snapshot(scope: str = "all") -> CatalogSnapshot:
    if not FOODS_PARQUET.is_file():
        raise FileNotFoundError(f"foods.parquet missing at {FOODS_PARQUET}")
    connection = duckdb.connect(":memory:")
    total = connection.execute(
        f"SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}') WHERE {scope_sql(scope)}"
    ).fetchone()[0]
    rows = connection.execute(
        f"""
        SELECT source, count(*) AS n
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE {scope_sql(scope)}
        GROUP BY source
        ORDER BY source
        """
    ).fetchall()
    return CatalogSnapshot(
        scope=scope,
        total_rows=int(total),
        source_counts={str(source): int(count) for source, count in rows},
    )


def open_index_table():
    if not INDEX_DIR.is_dir():
        raise FileNotFoundError(f"Index missing at {INDEX_DIR}")
    import lancedb

    db = lancedb.connect(str(INDEX_DIR))
    return db.open_table(TABLE_NAME)


def fetch_index_row(record_id: str) -> dict[str, Any] | None:
    table = open_index_table()
    rows = table.search().where(f"id = '{record_id}'").limit(1).to_list()
    return rows[0] if rows else None


def sample_parquet_ids(scope: str, *, count: int, seed: int) -> list[str]:
    snapshot = parquet_snapshot(scope)
    if snapshot.total_rows == 0:
        return []
    connection = duckdb.connect(":memory:")
    limit = min(count, snapshot.total_rows)
    rows = connection.execute(
        f"""
        SELECT id
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE {scope_sql(scope)}
        ORDER BY hash(id || '{seed}')
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    return [str(row[0]) for row in rows]
