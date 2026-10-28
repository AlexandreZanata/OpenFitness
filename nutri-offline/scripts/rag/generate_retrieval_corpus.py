#!/usr/bin/env python3
"""Generate stratified retrieval benchmark corpus — Phase 11 (N-11-14)."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import FOOD_ALIASES_PARQUET, FOODS_PARQUET
from build_index import scope_sql


def _query_rows(sql: str, params: list | None = None) -> list[dict]:
    connection = duckdb.connect(":memory:")
    rows = connection.execute(sql, params or []).fetchall()
    columns = [desc[0] for desc in connection.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def generate_corpus(*, seed: int = 110629) -> list[dict]:
    rng = random.Random(seed)
    parquet = FOODS_PARQUET.as_posix()
    corpus: list[dict] = []

    taco_rows = _query_rows(
        f"""
        SELECT id, name, source, name_normalized
        FROM read_parquet('{parquet}')
        WHERE source = 'taco'
        ORDER BY id
        """
    )
    for row in taco_rows:
        corpus.append(
            {
                "id": f"TACO-{row['id']}",
                "bucket": "taco",
                "query": row["name"],
                "expected_id": row["id"],
                "expected_source": "taco",
            }
        )
        if row.get("name_normalized") and row["name_normalized"] != row["name"]:
            corpus.append(
                {
                    "id": f"TACO-NORM-{row['id']}",
                    "bucket": "taco",
                    "query": row["name_normalized"],
                    "expected_id": row["id"],
                    "expected_source": "taco",
                }
            )

    off_rows = _query_rows(
        f"""
        SELECT id, name, source, brand
        FROM read_parquet('{parquet}')
        WHERE source = 'off' AND energy_kcal IS NOT NULL
        ORDER BY hash(id || '{seed}')
        LIMIT 5000
        """
    )
    rng.shuffle(off_rows)
    for row in off_rows[:500]:
        query = row["name"]
        if row.get("brand"):
            query = f"{row['brand']} {row['name']}"
        corpus.append(
            {
                "id": f"OFF-{row['id']}",
                "bucket": "off",
                "query": query,
                "expected_id": row["id"],
                "expected_source": "off",
            }
        )

    fdc_foundation = _query_rows(
        f"""
        SELECT id, name, source
        FROM read_parquet('{parquet}')
        WHERE source = 'fdc'
          AND json_extract_string(raw_metadata, '$.dataset') = 'foundation'
        ORDER BY hash(id || '{seed}')
        LIMIT 500
        """
    )
    for row in fdc_foundation[:200]:
        corpus.append(
            {
                "id": f"FDC-F-{row['id']}",
                "bucket": "fdc_foundation",
                "query": row["name"],
                "expected_id": row["id"],
                "expected_source": "fdc",
            }
        )

    fdc_branded = _query_rows(
        f"""
        SELECT id, name, source, brand
        FROM read_parquet('{parquet}')
        WHERE source = 'fdc' AND brand IS NOT NULL AND brand != ''
        ORDER BY hash(id || '{seed}')
        LIMIT 10000
        """
    )
    for row in fdc_branded[:2000]:
        brand = str(row.get("brand") or "")
        query = f"{brand} {row['name']}".strip()
        corpus.append(
            {
                "id": f"FDC-B-{row['id']}",
                "bucket": "fdc_branded",
                "query": query,
                "expected_id": row["id"],
                "expected_source": "fdc",
            }
        )

    if FOOD_ALIASES_PARQUET.is_file():
        alias_rows = _query_rows(
            f"""
            SELECT alias, record_id, source
            FROM read_parquet('{FOOD_ALIASES_PARQUET.as_posix()}')
            ORDER BY hash(alias || '{seed}')
            LIMIT 500
            """
        )
        for row in alias_rows[:100]:
            corpus.append(
                {
                    "id": f"ALIAS-{row['record_id']}-{row['alias'][:12]}",
                    "bucket": "alias",
                    "query": row["alias"],
                    "expected_id": row["record_id"],
                    "expected_source": row["source"],
                }
            )

    negatives = [
        "nutrizxyabc inventado 100g",
        "superfood lunar raro 200g",
        "alimento ficticio omega999",
        "xyz carboidrato impossivel",
        "produto inexistente nutri404",
    ]
    for index, query in enumerate(negatives * 10):
        corpus.append(
            {
                "id": f"NEG-{index:03d}",
                "bucket": "negative",
                "query": query,
                "expected_id": None,
                "expected_source": None,
            }
        )

    generic_pt = [
        ("GEN-ARROZ", "arroz 100g", "taco"),
        ("GEN-FEIJAO", "feijão 80g", "taco"),
        ("GEN-BANANA", "banana 100g", "taco"),
    ]
    for item_id, query, source in generic_pt:
        corpus.append(
            {
                "id": item_id,
                "bucket": "generic_pt",
                "query": query,
                "expected_id": None,
                "expected_source": source,
                "expect_top1_source": source,
            }
        )

    return corpus


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def gate_sample(corpus: list[dict], *, max_rows: int = 200, seed: int = 110629) -> list[dict]:
    rng = random.Random(seed)
    by_bucket: dict[str, list[dict]] = {}
    for row in corpus:
        by_bucket.setdefault(row["bucket"], []).append(row)

    sample: list[dict] = []
    quotas = {
        "taco": 40,
        "off": 40,
        "fdc_foundation": 20,
        "fdc_branded": 40,
        "alias": 20,
        "negative": 20,
        "generic_pt": 3,
    }
    for bucket, quota in quotas.items():
        pool = by_bucket.get(bucket, [])
        rng.shuffle(pool)
        sample.extend(pool[:quota])

    if len(sample) > max_rows:
        rng.shuffle(sample)
        sample = sample[:max_rows]
    return sample


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate retrieval benchmark corpus")
    parser.add_argument("--seed", type=int, default=110629)
    parser.add_argument(
        "--out-full",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "retrieval_corpus_full.jsonl",
    )
    parser.add_argument(
        "--out-gate",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "retrieval_gate_sample.jsonl",
    )
    args = parser.parse_args()

    if not FOODS_PARQUET.is_file():
        raise SystemExit(f"Missing {FOODS_PARQUET}")

    corpus = generate_corpus(seed=args.seed)
    write_jsonl(args.out_full, corpus)
    gate = gate_sample(corpus, seed=args.seed)
    write_jsonl(args.out_gate, gate)

    buckets: dict[str, int] = {}
    for row in corpus:
        buckets[row["bucket"]] = buckets.get(row["bucket"], 0) + 1
    print(f"Wrote {len(corpus)} queries -> {args.out_full}")
    print(f"Wrote {len(gate)} gate queries -> {args.out_gate}")
    print(f"Buckets: {buckets}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
