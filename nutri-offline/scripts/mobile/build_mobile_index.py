#!/usr/bin/env python3
"""Build sqlite-vec mobile index from tier parquet (N-08-05, N-08-06)."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import duckdb
import numpy as np

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
sys.path.insert(0, str(RAG_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mobile_paths import (  # noqa: E402
    FOOD_ALIASES_PARQUET,
    FOODS_PARQUET,
    LOG_DIR,
    MOBILE_EMBED_DIM,
    MOBILE_EMBED_MODEL,
    MOBILE_INDEX_DIR,
    MOBILE_RECORD_IDS_PARQUET,
    VECTORS_DB,
)
from embed import encode_texts, load_embedder, resolve_device  # noqa: E402
from mobile_sqlite import connect  # noqa: E402
from quantize import quantize_int8  # noqa: E402
from semantic_surfaces import SemanticSurface, generate_surfaces_for_record  # noqa: E402
from text_builder import build_embedding_text  # noqa: E402


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def load_mobile_records(
    *,
    foods_parquet: Path,
    mobile_ids_parquet: Path,
    aliases_parquet: Path,
) -> list[dict]:
    connection = duckdb.connect(":memory:")
    foods = foods_parquet.as_posix()
    ids = mobile_ids_parquet.as_posix()
    rows = connection.execute(
        f"""
        SELECT
            f.id, f.source, f.name, f.name_normalized,
            f.energy_kcal, f.protein_g, f.carbohydrate_g, f.fat_g, f.fiber_g,
            f.serving_basis, f.category, f.brand, m.tier
        FROM read_parquet('{ids}') m
        JOIN read_parquet('{foods}') f ON m.id = f.id
        ORDER BY m.tier, f.id
        """
    ).fetchall()

    alias_map: dict[str, list[str]] = {}
    if aliases_parquet.is_file():
        alias_rows = connection.execute(
            f"""
            SELECT a.record_id, a.alias
            FROM read_parquet('{aliases_parquet.as_posix()}') a
            JOIN read_parquet('{ids}') m ON a.record_id = m.id
            """
        ).fetchall()
        for record_id, alias in alias_rows:
            alias_map.setdefault(str(record_id), []).append(str(alias))

    records: list[dict] = []
    for row in rows:
        record_id = str(row[0])
        name = _text(row[2])
        name_normalized = _text(row[3])
        aliases = alias_map.get(record_id, [])
        search_text = " ".join(part for part in [name, name_normalized, " ".join(aliases)] if part)
        records.append(
            {
                "id": record_id,
                "source": str(row[1]),
                "name": name,
                "name_normalized": name_normalized,
                "energy_kcal": row[4],
                "protein_g": row[5],
                "carbohydrate_g": row[6],
                "fat_g": row[7],
                "fiber_g": row[8],
                "serving_basis": _text(row[9]) or "100g",
                "category": _text(row[10]),
                "brand": _text(row[11]),
                "tier": str(row[12]),
                "search_text": search_text,
            }
        )
    return records


def build_surface_rows(records: list[dict]) -> list[SemanticSurface]:
    surfaces: list[SemanticSurface] = []
    for record in records:
        surfaces.extend(
            generate_surfaces_for_record(
                record_id=record["id"],
                name=record["name"],
                name_normalized=record["name_normalized"],
                category=record["category"],
                source=record["source"],
                brand=record["brand"],
                tier=record["tier"],
                aliases=record.get("aliases", []),
            )
        )
    return surfaces


def build_vectors_db(
    records: list[dict],
    vectors: list[list[float]],
    *,
    output_path: Path,
    dims: int = MOBILE_EMBED_DIM,
    surfaces: list[SemanticSurface] | None = None,
    surface_vectors: list[list[float]] | None = None,
) -> dict:
    if output_path.exists():
        output_path.unlink()

    connection = connect(str(output_path))
    connection.execute(
        f"""
        CREATE TABLE food_meta (
            rowid INTEGER PRIMARY KEY,
            id TEXT NOT NULL UNIQUE,
            source TEXT,
            name TEXT,
            name_normalized TEXT,
            energy_kcal REAL,
            protein_g REAL,
            carbohydrate_g REAL,
            fat_g REAL,
            fiber_g REAL,
            serving_basis TEXT,
            category TEXT,
            brand TEXT,
            tier TEXT,
            search_text TEXT,
            embedding_int8 BLOB,
            quant_scale REAL
        )
        """
    )
    connection.execute(
        f"CREATE VIRTUAL TABLE food_vec USING vec0(embedding float32[{dims}])"
    )

    for index, (record, vector) in enumerate(zip(records, vectors, strict=True), start=1):
        int8_blob, scale = quantize_int8(vector)
        connection.execute(
            """
            INSERT INTO food_meta (
                rowid, id, source, name, name_normalized,
                energy_kcal, protein_g, carbohydrate_g, fat_g, fiber_g,
                serving_basis, category, brand, tier, search_text,
                embedding_int8, quant_scale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                index,
                record["id"],
                record["source"],
                record["name"],
                record["name_normalized"],
                record["energy_kcal"],
                record["protein_g"],
                record["carbohydrate_g"],
                record["fat_g"],
                record["fiber_g"],
                record["serving_basis"],
                record["category"],
                record["brand"],
                record["tier"],
                record["search_text"],
                int8_blob,
                scale,
            ),
        )
        connection.execute(
            "INSERT INTO food_vec(rowid, embedding) VALUES (?, ?)",
            (index, np.asarray(vector, dtype=np.float32)),
        )

    surface_count = 0
    if surfaces and surface_vectors:
        connection.execute(
            """
            CREATE TABLE food_surfaces (
                rowid INTEGER PRIMARY KEY,
                surface_id TEXT NOT NULL UNIQUE,
                record_id TEXT NOT NULL,
                surface_kind TEXT NOT NULL,
                search_text TEXT NOT NULL,
                embedding_int8 BLOB,
                quant_scale REAL
            )
            """
        )
        connection.execute(
            f"CREATE VIRTUAL TABLE food_surface_vec USING vec0(embedding float32[{dims}])"
        )
        connection.execute(
            "CREATE INDEX idx_food_surfaces_record ON food_surfaces(record_id)"
        )
        for index, (surface, vector) in enumerate(
            zip(surfaces, surface_vectors, strict=True), start=1
        ):
            int8_blob, scale = quantize_int8(vector)
            connection.execute(
                """
                INSERT INTO food_surfaces (
                    rowid, surface_id, record_id, surface_kind, search_text,
                    embedding_int8, quant_scale
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    index,
                    surface.surface_id,
                    surface.record_id,
                    surface.surface_kind,
                    surface.search_text,
                    int8_blob,
                    scale,
                ),
            )
            connection.execute(
                "INSERT INTO food_surface_vec(rowid, embedding) VALUES (?, ?)",
                (index, np.asarray(vector, dtype=np.float32)),
            )
        surface_count = len(surfaces)

    connection.commit()
    size_bytes = output_path.stat().st_size
    connection.close()
    return {
        "record_count": len(records),
        "surface_count": surface_count,
        "size_bytes": size_bytes,
    }


def recall_at_k(
    records: list[dict],
    vectors: list[list[float]],
    *,
    probes: list[str],
    embedder,
    k: int = 5,
) -> float:
    if not probes:
        return 1.0

    connection = connect(":memory:")
    dims = len(vectors[0])
    connection.execute(
        f"CREATE VIRTUAL TABLE probe_vec USING vec0(embedding float32[{dims}])"
    )
    for index, vector in enumerate(vectors, start=1):
        connection.execute(
            "INSERT INTO probe_vec(rowid, embedding) VALUES (?, ?)",
            (index, np.asarray(vector, dtype=np.float32)),
        )
    connection.execute(
        "CREATE TABLE ids (rowid INTEGER PRIMARY KEY, record_id TEXT)"
    )
    for index, record in enumerate(records, start=1):
        connection.execute(
            "INSERT INTO ids(rowid, record_id) VALUES (?, ?)",
            (index, record["id"]),
        )

    overlaps = 0
    for probe in probes:
        query_vec = encode_texts(embedder, [probe], show_progress=False)[0]
        float_rows = connection.execute(
            """
            SELECT rowid FROM probe_vec
            WHERE embedding MATCH ?
            ORDER BY distance LIMIT ?
            """,
            (np.asarray(query_vec, dtype=np.float32), k),
        ).fetchall()
        float_ids = {row[0] for row in float_rows}

        int8_scores: list[tuple[int, float]] = []
        for index, vector in enumerate(vectors, start=1):
            stored = np.asarray(vector, dtype=np.float32)
            query = np.asarray(query_vec, dtype=np.float32)
            score = float(np.dot(stored, query))
            int8_scores.append((index, score))
        int8_scores.sort(key=lambda item: item[1], reverse=True)
        int8_ids = {item[0] for item in int8_scores[:k]}

        overlaps += len(float_ids & int8_ids) / k

    connection.close()
    return overlaps / len(probes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build mobile sqlite-vec index")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--output", type=Path, default=VECTORS_DB)
    parser.add_argument(
        "--multi-surface",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Build food_surfaces + food_surface_vec tables (N-09-04)",
    )
    args = parser.parse_args()

    if not MOBILE_RECORD_IDS_PARQUET.is_file():
        print("ERROR: run select_mobile_records.py first", file=sys.stderr)
        return 1

    started = time.perf_counter()
    records = load_mobile_records(
        foods_parquet=FOODS_PARQUET,
        mobile_ids_parquet=MOBILE_RECORD_IDS_PARQUET,
        aliases_parquet=FOOD_ALIASES_PARQUET,
    )
    texts = [build_embedding_text(record) for record in records]

    device = resolve_device(args.device)
    model = load_embedder(device, model_name=MOBILE_EMBED_MODEL)
    vectors = encode_texts(model, texts, batch_size=args.batch_size)

    surfaces: list[SemanticSurface] = []
    surface_vectors: list[list[float]] | None = None
    if args.multi_surface:
        surfaces = build_surface_rows(records)
        surface_texts = [surface.search_text for surface in surfaces]
        surface_vectors = encode_texts(model, surface_texts, batch_size=args.batch_size)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    summary = build_vectors_db(
        records,
        vectors,
        output_path=args.output,
        surfaces=surfaces if args.multi_surface else None,
        surface_vectors=surface_vectors,
    )

    probes = [
        "arroz cozido",
        "feijão preto",
        "banana prata",
        "frango grelhado",
        "ovo cozido",
        "iogurte vigor",
    ]
    recall = recall_at_k(records, vectors, probes=probes, embedder=model, k=5)
    elapsed = time.perf_counter() - started

    tier_counts = {"taco": 0, "tbca": 0, "off_tier_c": 0}
    for record in records:
        source = record["source"]
        if source == "taco":
            tier_counts["taco"] += 1
        elif source == "tbca":
            tier_counts["tbca"] += 1
        elif source == "off":
            tier_counts["off_tier_c"] += 1

    report = {
        **summary,
        "tiers": tier_counts,
        "vector_format": "float32_vec0+int8_blob",
        "dims": MOBILE_EMBED_DIM,
        "recall_at_5_overlap": round(recall, 4),
        "build_seconds": round(elapsed, 2),
        "output": str(args.output),
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "mobile-index-build.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    if recall < 0.95:
        print(f"WARN: recall@5 overlap {recall:.2%} below 95% target", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
