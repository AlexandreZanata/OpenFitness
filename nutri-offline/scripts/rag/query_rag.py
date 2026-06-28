#!/usr/bin/env python3
"""Query NutriOffline LanceDB RAG index."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import lancedb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import INDEX_DIR, INDEX_METADATA, TABLE_NAME
from embed import encode_texts, load_embedder, resolve_device


@dataclass
class RagResult:
    score: float
    id: str
    name: str
    source: str
    rag_context: str
    metadata: dict[str, Any]


def open_table():
    if not INDEX_DIR.exists():
        raise FileNotFoundError(f"Index missing at {INDEX_DIR} — run build_index.py first")
    db = lancedb.connect(str(INDEX_DIR))
    return db.open_table(TABLE_NAME)


def search(
    query: str,
    *,
    top_k: int = 5,
    device: str = "cpu",
) -> list[RagResult]:
    table = open_table()
    model = load_embedder(resolve_device(device))
    vector = encode_texts(model, [query], show_progress=False)[0]

    results = (
        table.search(vector, vector_column_name="vector")
        .limit(top_k)
        .to_list()
    )

    rag_results: list[RagResult] = []
    for row in results:
        score = row.get("_distance")
        if score is not None:
            score = 1.0 - float(score)
        rag_results.append(
            RagResult(
                score=float(score or 0.0),
                id=row["id"],
                name=row["name"],
                source=row["source"],
                rag_context=row["rag_context"],
                metadata={
                    "energy_kcal": row.get("energy_kcal"),
                    "protein_g": row.get("protein_g"),
                    "carbohydrate_g": row.get("carbohydrate_g"),
                    "fat_g": row.get("fat_g"),
                },
            )
        )
    return rag_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Query NutriOffline RAG index")
    parser.add_argument("query", help="Natural language query (PT-BR or EN)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    started = time.perf_counter()
    results = search(args.query, top_k=args.top_k, device=args.device)
    elapsed_ms = (time.perf_counter() - started) * 1000

    if args.json:
        payload = {
            "query": args.query,
            "latency_ms": round(elapsed_ms, 2),
            "results": [asdict(item) for item in results],
        }
        if INDEX_METADATA.exists():
            payload["index_metadata"] = json.loads(INDEX_METADATA.read_text(encoding="utf-8"))
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Query: {args.query}")
    print(f"Latency: {elapsed_ms:.1f} ms\n")
    for index, item in enumerate(results, start=1):
        print(f"{index}. [{item.source}] {item.name} (score={item.score:.4f})")
        print(f"   {item.rag_context}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
