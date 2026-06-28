#!/usr/bin/env python3
"""Dataset statistics report (Phase 4)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import GENERATION_LOG, RAW_GENERATED, STATS_JSON, TRAIN_JSONL, VAL_JSONL


def load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def build_stats(examples: list[dict], train_count: int, val_count: int) -> dict:
    categories = Counter()
    sources = Counter()
    languages = Counter()
    answer_lengths: list[int] = []
    token_estimates: list[int] = []

    for example in examples:
        log = example if "category" in example else example.get("generation_log", {})
        if "category" not in log and "generation_log" in example:
            log = example["generation_log"]
        categories[log.get("category", "unknown")] += 1
        languages[log.get("language", "pt")] += 1
        grounding = log.get("grounding", {})
        for record_id in grounding.get("record_ids") or []:
            sources[record_id.split(":")[0]] += 1

        messages = example.get("messages") or []
        if messages:
            full_text = " ".join(m["content"] for m in messages)
            answer_lengths.append(len(messages[-1]["content"]))
            token_estimates.append(estimate_tokens(full_text))

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_examples": len(examples),
        "train_examples": train_count,
        "val_examples": val_count,
        "by_category": dict(categories),
        "by_language": dict(languages),
        "by_source_mentions": dict(sources),
        "avg_answer_length_chars": round(sum(answer_lengths) / max(len(answer_lengths), 1), 1),
        "max_answer_length_chars": max(answer_lengths) if answer_lengths else 0,
        "avg_tokens_estimate": round(sum(token_estimates) / max(len(token_estimates), 1), 1),
        "max_tokens_estimate": max(token_estimates) if token_estimates else 0,
        "fits_2048_context": max(token_estimates) <= 2048 if token_estimates else True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    if not RAW_GENERATED.exists():
        print(f"ERROR: {RAW_GENERATED} missing", flush=True)
        return 1

    examples = load_jsonl(RAW_GENERATED)
    train_count = len(load_jsonl(TRAIN_JSONL)) if TRAIN_JSONL.exists() else 0
    val_count = len(load_jsonl(VAL_JSONL)) if VAL_JSONL.exists() else 0
    stats = build_stats(examples, train_count, val_count)

    STATS_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATS_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
