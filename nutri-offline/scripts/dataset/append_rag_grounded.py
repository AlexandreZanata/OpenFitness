#!/usr/bin/env python3
"""Append RAG-grounded ChatML examples to train.jsonl (N-05-08 boost)."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from answers import generate_direct_lookup, generate_household_portion, source_label
from constants import SYSTEM_PROMPT
from records import connect, fetch_records_by_ids

TRAIN_JSONL = Path(__file__).resolve().parents[2] / "data" / "datasets" / "train.jsonl"

RAG_SCENARIOS = [
    {
        "question": "Quantas calorias tem a porção abaixo?",
        "rag_context": "Alimento: Manga, palmer (1 unidade, 230g)\nFonte: TACO (NEPA/UNICAMP)\nCalorias: 146 kcal",
        "record_id": "taco:228",
        "portion_g": 230,
        "unit_label": "uma manga inteira",
    },
    {
        "question": "Quantas calorias tem este item?",
        "rag_context": "Alimento: Pão, francês (50g)\nFonte: TACO (NEPA/UNICAMP)\nCalorias: 150 kcal",
        "record_id": "taco:53",
        "portion_g": 50,
        "unit_label": "50g de pão francês",
    },
]


def build_rag_example(
    *,
    question: str,
    rag_context: str,
    assistant: str,
) -> dict:
    return {
        "messages": [
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\n\nContext (use estes valores com precisão):\n{rag_context}",
            },
            {"role": "user", "content": question},
            {"role": "assistant", "content": assistant},
        ]
    }


def main() -> int:
    connection = connect()
    records = fetch_records_by_ids(connection, [s["record_id"] for s in RAG_SCENARIOS])
    extra: list[dict] = []

    for scenario in RAG_SCENARIOS:
        record = records[scenario["record_id"]]
        for _ in range(40):
            if scenario.get("portion_g") != 100:
                answer, _ = generate_household_portion(
                    record,
                    portion_g=int(scenario["portion_g"]),
                    unit_label=str(scenario["unit_label"]),
                    template_language="pt",
                )
            else:
                answer, _ = generate_direct_lookup(record, "pt")
            extra.append(
                build_rag_example(
                    question=scenario["question"],
                    rag_context=scenario["rag_context"],
                    assistant=answer,
                )
            )

    existing = [
        json.loads(line)
        for line in TRAIN_JSONL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    merged = existing + extra
    with TRAIN_JSONL.open("w", encoding="utf-8") as handle:
        for row in merged:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Appended {len(extra)} RAG-grounded examples -> {TRAIN_JSONL} (total {len(merged)})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
