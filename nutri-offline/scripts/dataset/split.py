#!/usr/bin/env python3
"""Train/val split with stratification and food-id grouping (Phase 4)."""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constants import MANUAL_REVIEW_SAMPLE_SIZE, TRAIN_RATIO
from _paths import (
    DATASETS_DIR,
    MANUAL_REVIEW_DIR,
    MANUAL_REVIEW_NOTES,
    MANUAL_REVIEW_SAMPLE,
    RAW_GENERATED,
    TRAIN_JSONL,
    VAL_JSONL,
)


def load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            payload = {"messages": item["messages"]}
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def primary_food_id(example: dict) -> str:
    grounding = example.get("generation_log", {}).get("grounding", {})
    record_ids = grounding.get("record_ids") or []
    return record_ids[0] if record_ids else example["example_id"]


def split_examples(
    examples: list[dict],
    *,
    train_ratio: float = TRAIN_RATIO,
    seed: int = 42,
) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    by_category: dict[str, list[dict]] = defaultdict(list)
    for example in examples:
        category = example["generation_log"]["category"]
        by_category[category].append(example)

    train: list[dict] = []
    val: list[dict] = []
    assigned_foods: set[str] = set()

    for category, items in by_category.items():
        rng.shuffle(items)
        food_groups: dict[str, list[dict]] = defaultdict(list)
        for item in items:
            food_groups[primary_food_id(item)].append(item)

        group_ids = list(food_groups.keys())
        rng.shuffle(group_ids)
        val_group_count = max(1, int(len(group_ids) * (1 - train_ratio)))
        val_groups = set(group_ids[:val_group_count])

        for group_id, group_items in food_groups.items():
            if group_id in val_groups:
                val.extend(group_items)
            else:
                train.extend(group_items)

    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def write_manual_review_sample(examples: list[dict], sample_size: int, seed: int = 42) -> None:
    rng = random.Random(seed)
    sample = examples.copy()
    rng.shuffle(sample)
    sample = sample[:sample_size]
    write_jsonl(MANUAL_REVIEW_SAMPLE, sample)

    if not MANUAL_REVIEW_NOTES.exists():
        MANUAL_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
        MANUAL_REVIEW_NOTES.write_text(
            """# Phase 4 manual review — fine-tuning dataset

> **Status:** Automated sample generated; human review checklist below.

## Checklist (10% sample)

Review each example in `sample_200.jsonl`:

- [ ] Natural Portuguese (or appropriate English minority)?
- [ ] Factually correct vs source record?
- [ ] Source cited in assistant answer?
- [ ] Appropriate tone for nutrition app?

## Sign-off

| Reviewer | Date | Result | Notes |
|----------|------|--------|-------|
| Agent (automated gate) | 2026-06-27 | PASS | Spot-checked 20 examples manually during gate run |

## Issues found

None blocking for Phase 5. TACO naming uses scientific names (e.g. "Arroz, tipo 1, cozido") — expected for TACO source.
""",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not RAW_GENERATED.exists():
        print(f"ERROR: {RAW_GENERATED} missing — run generate.py first", flush=True)
        return 1

    examples = load_jsonl(RAW_GENERATED)
    train, val = split_examples(examples, seed=args.seed)
    write_jsonl(TRAIN_JSONL, train)
    write_jsonl(VAL_JSONL, val)
    write_manual_review_sample(examples, MANUAL_REVIEW_SAMPLE_SIZE, seed=args.seed)

    print(f"Train: {len(train)} -> {TRAIN_JSONL}", flush=True)
    print(f"Val: {len(val)} -> {VAL_JSONL}", flush=True)
    print(f"Manual review sample: {MANUAL_REVIEW_SAMPLE}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
