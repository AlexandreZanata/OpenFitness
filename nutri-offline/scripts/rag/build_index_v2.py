#!/usr/bin/env python3
"""Build LanceDB vector index v2 with FTS and structured metadata (RAG-V2-09)."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import lancedb
import pyarrow as pa

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import (
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    FOOD_ALIASES_PARQUET,
    FOODS_PARQUET,
    INDEX_DIR,
    INDEX_METADATA,
    LOG_DIR,
    SCHEMA_VERSION_V2,
    SCOPE_ALL_SQL,
    SCOPE_V1_SQL,
    TABLE_NAME,
)
from build_index import CHUNK_SIZE, scope_sql, sha256_file
from embed import DEFAULT_BATCH_SIZE, encode_texts, load_embedder, resolve_device
from text_builder import build_embedding_text, build_rag_context


def source_tier(source: str) -> int:
    if source in {"taco", "tbca"}:
        return 1
    if source == "fdc":
        return 2
    return 3


def is_generic_record(record: dict) -> bool:
    return record["source"] in {"taco", "tbca"} and not record.get("brand")


def load_alias_map() -> dict[str, list[str]]:
    if not FOOD_ALIASES_PARQUET.is_file():
        return {}
    connection = duckdb.connect(":memory:")
    rows = connection.execute(
        f"""
        SELECT record_id, alias
        FROM read_parquet('{FOOD_ALIASES_PARQUET.as_posix()}')
        ORDER BY record_id, priority, alias
        """
    ).fetchall()
    alias_map: dict[str, list[str]] = {}
    for record_id, alias in rows:
        alias_map.setdefault(str(record_id), [])
        if str(alias) not in alias_map[str(record_id)]:
            alias_map[str(record_id)].append(str(alias))
    return alias_map


def ensure_aliases() -> None:
    if FOOD_ALIASES_PARQUET.is_file():
        return
    script = Path(__file__).resolve().parent / "build_food_aliases.py"
    subprocess.run([sys.executable, str(script)], check=True)


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def records_to_rows_v2(
    records: list[dict],
    vectors: list[list[float]],
    alias_map: dict[str, list[str]],
) -> pa.Table:
    rows = {
        "id": [],
        "vector": [],
        "name": [],
        "name_normalized": [],
        "source": [],
        "source_tier": [],
        "is_generic": [],
        "aliases": [],
        "search_text": [],
        "serving_basis": [],
        "energy_kcal": [],
        "protein_g": [],
        "carbohydrate_g": [],
        "fat_g": [],
        "embedding_text": [],
        "rag_context": [],
    }
    for record, vector in zip(records, vectors, strict=True):
        record_id = str(record["id"])
        aliases = alias_map.get(record_id, [])
        name_normalized = _text(record.get("name_normalized"))
        name = _text(record.get("name"))
        search_text = " ".join(
            part for part in [name, name_normalized, " ".join(aliases)] if part
        )
        rows["id"].append(record_id)
        rows["vector"].append(vector)
        rows["name"].append(name)
        rows["name_normalized"].append(name_normalized)
        rows["source"].append(str(record["source"]))
        rows["source_tier"].append(source_tier(str(record["source"])))
        rows["is_generic"].append(is_generic_record(record))
        rows["aliases"].append(";".join(aliases))
        rows["search_text"].append(search_text)
        rows["serving_basis"].append(str(record.get("serving_basis") or "100g"))
        rows["energy_kcal"].append(record.get("energy_kcal"))
        rows["protein_g"].append(record.get("protein_g"))
        rows["carbohydrate_g"].append(record.get("carbohydrate_g"))
        rows["fat_g"].append(record.get("fat_g"))
        rows["embedding_text"].append(record["embedding_text"])
        rows["rag_context"].append(record["rag_context"])

    return pa.table(
        {
            "id": pa.array(rows["id"], type=pa.string()),
            "vector": pa.array(rows["vector"], type=pa.list_(pa.float32(), EMBEDDING_DIM)),
            "name": pa.array(rows["name"], type=pa.string()),
            "name_normalized": pa.array(rows["name_normalized"], type=pa.string()),
            "source": pa.array(rows["source"], type=pa.string()),
            "source_tier": pa.array(rows["source_tier"], type=pa.int32()),
            "is_generic": pa.array(rows["is_generic"], type=pa.bool_()),
            "aliases": pa.array(rows["aliases"], type=pa.string()),
            "search_text": pa.array(rows["search_text"], type=pa.string()),
            "serving_basis": pa.array(rows["serving_basis"], type=pa.string()),
            "energy_kcal": pa.array(rows["energy_kcal"], type=pa.float64()),
            "protein_g": pa.array(rows["protein_g"], type=pa.float64()),
            "carbohydrate_g": pa.array(rows["carbohydrate_g"], type=pa.float64()),
            "fat_g": pa.array(rows["fat_g"], type=pa.float64()),
            "embedding_text": pa.array(rows["embedding_text"], type=pa.string()),
            "rag_context": pa.array(rows["rag_context"], type=pa.string()),
        }
    )


def fetch_chunk_v2(connection: duckdb.DuckDBPyConnection, scope: str, offset: int, limit: int):
    parquet = FOODS_PARQUET.as_posix()
    return connection.execute(
        f"""
        SELECT
            id, source, name, name_normalized, category, brand, serving_basis,
            energy_kcal, protein_g, carbohydrate_g, fat_g,
            fiber_g, sodium_mg, sugar_g, ingredients_text
        FROM read_parquet('{parquet}')
        WHERE {scope_sql(scope)}
        ORDER BY id
        LIMIT {limit} OFFSET {offset}
        """
    ).fetchdf()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build NutriOffline LanceDB RAG index v2")
    parser.add_argument("--scope", choices=["v1", "all"], default="v1")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, or auto")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--skip-aliases", action="store_true")
    args = parser.parse_args()

    if not FOODS_PARQUET.exists():
        raise SystemExit(f"Missing {FOODS_PARQUET} — run Phase 2 first")

    if not args.skip_aliases:
        ensure_aliases()

    alias_map = load_alias_map()
    log_path = LOG_DIR / f"build-index-v2-{datetime.now().strftime('%Y-%m-%d')}.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(":memory:")
    parquet = FOODS_PARQUET.as_posix()
    total = connection.execute(
        f"SELECT count(*) FROM read_parquet('{parquet}') WHERE {scope_sql(args.scope)}"
    ).fetchone()[0]

    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    device = resolve_device(args.device)
    model = load_embedder(device)
    db = lancedb.connect(str(INDEX_DIR))
    table = None
    built = 0
    started = time.monotonic()

    offset = 0
    while offset < total:
        chunk = fetch_chunk_v2(connection, args.scope, offset, args.chunk_size)
        if chunk.empty:
            break

        records: list[dict] = []
        for row in chunk.to_dict(orient="records"):
            item = dict(row)
            item["embedding_text"] = build_embedding_text(item)
            item["rag_context"] = build_rag_context(item)
            records.append(item)

        texts = [record["embedding_text"] for record in records]
        vectors = encode_texts(
            model,
            texts,
            batch_size=args.batch_size,
            show_progress=offset == 0,
        )
        arrow_batch = records_to_rows_v2(records, vectors, alias_map)

        if table is None:
            table = db.create_table(TABLE_NAME, arrow_batch, mode="overwrite")
        else:
            table.add(arrow_batch)

        built += len(records)
        offset += args.chunk_size
        message = f"Indexed v2 {built:,}/{total:,} records"
        print(message, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    if table is None or built == 0:
        raise SystemExit("FAIL: no records indexed")

    if built > 100_000:
        table.create_index(metric="cosine", vector_column_name="vector", replace=True)

    table.create_fts_index("search_text", replace=True)

    elapsed = time.monotonic() - started
    index_size_mb = sum(
        file.stat().st_size for file in INDEX_DIR.rglob("*") if file.is_file()
    ) / (1024 * 1024)

    source_counts = {
        str(row[0]): int(row[1])
        for row in connection.execute(
            f"""
            SELECT source, count(*) AS n
            FROM read_parquet('{parquet}')
            WHERE {scope_sql(args.scope)}
            GROUP BY source
            ORDER BY source
            """
        ).fetchall()
    }

    metadata = {
        "schema_version": SCHEMA_VERSION_V2,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dim": EMBEDDING_DIM,
        "record_count": built,
        "scope": args.scope,
        "source_counts": source_counts,
        "device": device,
        "batch_size": args.batch_size,
        "build_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "build_seconds": round(elapsed, 2),
        "foods_parquet_sha256": sha256_file(FOODS_PARQUET),
        "food_aliases_sha256": sha256_file(FOOD_ALIASES_PARQUET) if FOOD_ALIASES_PARQUET.is_file() else None,
        "lancedb_version": lancedb.__version__,
        "index_size_mb": round(index_size_mb, 2),
        "vector_index": built > 100_000,
        "fts_index": True,
    }
    INDEX_METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(
        f"PASS: index v2 built — {built:,} records, {index_size_mb:.1f} MB, "
        f"{elapsed:.1f}s, FTS on search_text -> {INDEX_DIR}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
