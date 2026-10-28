#!/usr/bin/env python3
"""Generate domain eval v2 fixtures — Phase 11 (N-11-20, N-11-23)."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
RAG_DIR = ROOT / "scripts" / "rag"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RAG_DIR))

from _paths import FOODS_PARQUET  # noqa: E402 — rag _paths

V1_FIXTURE = ROOT / "tests" / "fixtures" / "domain_eval_prompts.jsonl"
OUT_200 = ROOT / "tests" / "fixtures" / "domain_eval_v2_200.jsonl"
OUT_GATE = ROOT / "tests" / "fixtures" / "domain_eval_gate_v2.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def sample_fdc_branded(connection: duckdb.DuckDBPyConnection, *, limit: int, seed: int) -> list[dict]:
    parquet = FOODS_PARQUET.as_posix()
    rows = connection.execute(
        f"""
        SELECT id, name, brand, energy_kcal
        FROM read_parquet('{parquet}')
        WHERE source = 'fdc' AND brand IS NOT NULL AND brand != ''
          AND energy_kcal IS NOT NULL
        ORDER BY hash(id || '{seed}')
        LIMIT {limit * 3}
        """
    ).fetchall()
    rng = random.Random(seed)
    rng.shuffle(rows)
    prompts: list[dict] = []
    for index, (record_id, name, brand, kcal) in enumerate(rows[:limit]):
        prompts.append(
            {
                "id": f"V2-FDC-B-{index + 1:03d}",
                "category": "branded_fdc",
                "question": f"Quantas calorias tem {brand} {name} por 100g?",
                "expects_source_citation": True,
                "expects_number": float(kcal),
                "number_tolerance_pct": 15,
                "expected_record_id": record_id,
                "require_rag": True,
            }
        )
    return prompts


def sample_off_branded(connection: duckdb.DuckDBPyConnection, *, limit: int, seed: int) -> list[dict]:
    parquet = FOODS_PARQUET.as_posix()
    rows = connection.execute(
        f"""
        SELECT id, name, brand, energy_kcal
        FROM read_parquet('{parquet}')
        WHERE source = 'off' AND energy_kcal IS NOT NULL
        ORDER BY hash(id || '{seed}')
        LIMIT {limit * 3}
        """
    ).fetchall()
    rng = random.Random(seed)
    rng.shuffle(rows)
    prompts: list[dict] = []
    for index, (record_id, name, brand, kcal) in enumerate(rows[:limit]):
        brand_text = brand or "produto"
        prompts.append(
            {
                "id": f"V2-OFF-{index + 1:03d}",
                "category": "branded_off",
                "question": f"Informações nutricionais de {brand_text} {name}",
                "expects_source_citation": True,
                "expects_number": float(kcal),
                "number_tolerance_pct": 15,
                "expected_record_id": record_id,
                "require_rag": True,
            }
        )
    return prompts


def variant_prompts() -> list[dict]:
    return [
        {
            "id": "V2-VAR-001",
            "category": "variant",
            "question": "Quantas calorias tem 100g de frango grelhado?",
            "expects_source_citation": True,
            "expects_number": 159,
            "number_tolerance_pct": 8,
            "expected_record_id": "taco:410",
            "forbidden_record_ids": ["taco:414", "taco:415"],
            "require_rag": True,
        },
        {
            "id": "V2-VAR-002",
            "category": "variant",
            "question": "Quanto de proteína tem 100g de peito de frango grelhado?",
            "expects_source_citation": True,
            "expects_number": 32,
            "number_tolerance_pct": 8,
            "expected_record_id": "taco:410",
            "forbidden_record_ids": ["taco:414"],
            "require_rag": True,
        },
        {
            "id": "V2-VAR-003",
            "category": "variant",
            "question": "Quantas calorias tem 100g de arroz branco cozido?",
            "expects_source_citation": True,
            "expects_number": 128,
            "number_tolerance_pct": 5,
            "expected_record_id": "taco:1",
            "require_rag": True,
        },
        {
            "id": "V2-VAR-004",
            "category": "variant",
            "question": "Quantas calorias tem 100g de arroz branco cru?",
            "expects_source_citation": True,
            "expects_answer_contains": "arroz",
            "expected_record_id": "taco:2",
            "require_rag": True,
        },
        {
            "id": "V2-VAR-005",
            "category": "variant",
            "question": "Quantas calorias tem 100g de banana prata crua?",
            "expects_source_citation": True,
            "expects_number": 98,
            "number_tolerance_pct": 8,
            "expected_record_id": "taco:41",
            "require_rag": True,
        },
    ]


def compare_substitute_prompts() -> list[dict]:
    base = [
        {
            "id": "V2-CMP-001",
            "category": "comparison",
            "question": "Qual tem mais proteína: frango grelhado ou ovo cozido?",
            "expects_source_citation": True,
            "expects_answer_contains": "frango",
            "require_rag": True,
        },
        {
            "id": "V2-CMP-002",
            "category": "comparison",
            "question": "Qual tem mais calorias: arroz cozido ou feijão cozido?",
            "expects_source_citation": True,
            "expects_answer_contains": "arroz",
            "require_rag": True,
        },
        {
            "id": "V2-SUB-001",
            "category": "substitution",
            "question": "Existe opção mais leve que arroz branco cozido?",
            "expects_source_citation": True,
            "require_rag": True,
        },
        {
            "id": "V2-SUB-002",
            "category": "substitution",
            "question": "arroz com menos carboidrato",
            "expects_source_citation": True,
            "forbidden_record_ids": ["taco:29"],
            "require_rag": True,
        },
    ]
    return base


def unknown_prompts(count: int = 50, *, seed: int) -> list[dict]:
    rng = random.Random(seed)
    templates = [
        "Quantas calorias tem 100g de {food}?",
        "Quanto de proteína tem {food} por 100g?",
        "Informe macros de {food} inventado",
    ]
    foods = [f"nutrixyz{index}" for index in range(count)]
    rows: list[dict] = []
    for index, food in enumerate(foods):
        template = templates[index % len(templates)]
        rows.append(
            {
                "id": f"V2-UNK-{index + 1:03d}",
                "category": "unknown",
                "question": template.format(food=food),
                "require_rag": True,
            }
        )
    rng.shuffle(rows)
    return rows


def household_prompts() -> list[dict]:
    return [
        {
            "id": "V2-HH-001",
            "category": "household",
            "question": "Quantas calorias tem uma banana?",
            "expects_source_citation": True,
            "expects_number": 84,
            "number_tolerance_pct": 8,
            "require_rag": True,
        },
        {
            "id": "V2-HH-002",
            "category": "household",
            "question": "Quantas calorias tem um ovo?",
            "expects_source_citation": True,
            "expects_number": 73,
            "number_tolerance_pct": 8,
            "require_rag": True,
        },
        {
            "id": "V2-HH-003",
            "category": "household",
            "question": "Quantas calorias tem um cacetinho?",
            "expects_source_citation": True,
            "expects_number": 150,
            "number_tolerance_pct": 10,
            "require_rag": True,
        },
    ]


def build_v2_200(*, seed: int = 110629) -> list[dict]:
    connection = duckdb.connect(":memory:")
    base = load_jsonl(V1_FIXTURE)
    for row in base:
        row.setdefault("require_rag", True)

    extras: list[dict] = []
    extras.extend(variant_prompts())
    extras.extend(household_prompts())
    extras.extend(compare_substitute_prompts())
    extras.extend(sample_off_branded(connection, limit=40, seed=seed))
    extras.extend(sample_fdc_branded(connection, limit=40, seed=seed + 1))
    extras.extend(unknown_prompts(50, seed=seed + 2))

    # Pad with v1-style format/numeric until 200
    combined = base + extras
    seen_ids = {row["id"] for row in combined}
    counter = 1
    while len(combined) < 200:
        row = dict(base[counter % len(base)])
        row["id"] = f"V2-PAD-{counter:03d}"
        if row["id"] not in seen_ids:
            row["require_rag"] = True
            combined.append(row)
            seen_ids.add(row["id"])
        counter += 1

    return combined[:200]


def build_gate_v2(full: list[dict]) -> list[dict]:
    """25-prompt fast gate stratified from v2 set."""
    picks: list[dict] = []
    seen: set[str] = set()
    buckets = ["variant", "household", "comparison", "substitution", "unknown", "branded_off", "branded_fdc", "format", "numeric"]
    per_bucket = max(1, 25 // len(buckets))
    for bucket in buckets:
        if bucket in {"format", "numeric"}:
            pool = [row for row in full if row.get("category") in {"format", "numeric"}]
        else:
            pool = [row for row in full if row.get("category") == bucket]
        for row in pool[:per_bucket]:
            if row["id"] not in seen:
                picks.append(row)
                seen.add(row["id"])
    for row in full:
        if len(picks) >= 25:
            break
        if row["id"] not in seen:
            picks.append(row)
            seen.add(row["id"])
    return picks[:25]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=110629)
    args = parser.parse_args()

    if not V1_FIXTURE.is_file():
        raise SystemExit(f"Missing {V1_FIXTURE}")
    if not FOODS_PARQUET.is_file():
        raise SystemExit(f"Missing {FOODS_PARQUET}")

    full = build_v2_200(seed=args.seed)
    gate = build_gate_v2(full)
    write_jsonl(OUT_200, full)
    write_jsonl(OUT_GATE, gate)
    print(f"Wrote {len(full)} prompts -> {OUT_200}")
    print(f"Wrote {len(gate)} gate prompts -> {OUT_GATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
