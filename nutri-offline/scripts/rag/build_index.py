#!/usr/bin/env python3
"""Build LanceDB vector index from foods.parquet."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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
    FOODS_PARQUET,
    INDEX_DIR,
    INDEX_METADATA,
    LOG_DIR,
    SCOPE_ALL_SQL,
    SCOPE_V1_SQL,
    TABLE_NAME,
)
from embed import DEFAULT_BATCH_SIZE, encode_texts, load_embedder, resolve_device
from text_builder import build_embedding_text, build_rag_context

CHUNK_SIZE = 10_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def scope_sql(scope: str) -> str:
    if scope == "all":
        return SCOPE_ALL_SQL
    if scope == "v1":
        return SCOPE_V1_SQL
    raise ValueError(f"Unknown scope: {scope}")


def fetch_chunk(connection: duckdb.DuckDBPyConnection, scope: str, offset: int, limit: int):
    parquet = FOODS_PARQUET.as_posix()
    return connection.execute(
        f"""
        SELECT
            id, source, name, category, brand, serving_basis,
            energy_kcal, protein_g, carbohydrate_g, fat_g,
            fiber_g, sodium_mg, sugar_g, ingredients_text
        FROM read_parquet('{parquet}')
        WHERE {scope_sql(scope)}
        ORDER BY id
        LIMIT {limit} OFFSET {offset}
        """
    ).fetchdf()


def records_to_rows(records: list[dict], vectors: list[list[float]]) -> pa.Table:
    rows = {
        "id": [],
        "vector": [],
        "name": [],
        "source": [],
        "energy_kcal": [],
        "protein_g": [],
        "carbohydrate_g": [],
        "fat_g": [],
        "embedding_text": [],
        "rag_context": [],
    }
    for record, vector in zip(records, vectors, strict=True):
        rows["id"].append(str(record["id"]))
        rows["vector"].append(vector)
        rows["name"].append(str(record["name"]) if record["name"] is not None else "")
        rows["source"].append(str(record["source"]))
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
            "source": pa.array(rows["source"], type=pa.string()),
            "energy_kcal": pa.array(rows["energy_kcal"], type=pa.float64()),
            "protein_g": pa.array(rows["protein_g"], type=pa.float64()),
            "carbohydrate_g": pa.array(rows["carbohydrate_g"], type=pa.float64()),
            "fat_g": pa.array(rows["fat_g"], type=pa.float64()),
            "embedding_text": pa.array(rows["embedding_text"], type=pa.string()),
            "rag_context": pa.array(rows["rag_context"], type=pa.string()),
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build NutriOffline LanceDB RAG index")
    parser.add_argument("--scope", choices=["v1", "all"], default="v1")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, or auto")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    args = parser.parse_args()

    if not FOODS_PARQUET.exists():
        raise SystemExit(f"Missing {FOODS_PARQUET} — run Phase 2 first")

    log_path = LOG_DIR / f"build-index-{datetime.now().strftime('%Y-%m-%d')}.log"
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
        chunk = fetch_chunk(connection, args.scope, offset, args.chunk_size)
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
        arrow_batch = records_to_rows(records, vectors)

        if table is None:
            table = db.create_table(TABLE_NAME, arrow_batch, mode="overwrite")
        else:
            table.add(arrow_batch)

        built += len(records)
        offset += args.chunk_size
        message = f"Indexed {built:,}/{total:,} records"
        print(message, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    if table is None or built == 0:
        raise SystemExit("FAIL: no records indexed")

    if built > 100_000:
        table.create_index(metric="cosine", vector_column_name="vector", replace=True)

    elapsed = time.monotonic() - started
    index_size_mb = sum(
        file.stat().st_size for file in INDEX_DIR.rglob("*") if file.is_file()
    ) / (1024 * 1024)

    metadata = {
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dim": EMBEDDING_DIM,
        "record_count": built,
        "scope": args.scope,
        "device": device,
        "batch_size": args.batch_size,
        "build_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "build_seconds": round(elapsed, 2),
        "foods_parquet_sha256": sha256_file(FOODS_PARQUET),
        "lancedb_version": lancedb.__version__,
        "index_size_mb": round(index_size_mb, 2),
        "vector_index": built > 100_000,
    }
    INDEX_METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(
        f"PASS: index built — {built:,} records, {index_size_mb:.1f} MB, {elapsed:.1f}s -> {INDEX_DIR}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
