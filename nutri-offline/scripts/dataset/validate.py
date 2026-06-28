#!/usr/bin/env python3
"""Phase 4 validation gate — grounding, counts, stratification."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constants import MIN_TRAIN_EXAMPLES, MIN_VAL_EXAMPLES
from grounding import validate_all
from _paths import (
    MANUAL_REVIEW_SAMPLE,
    RAW_GENERATED,
    STATS_JSON,
    TRAIN_JSONL,
    VAL_JSONL,
)

LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "validate-dataset.log"


def log(message: str) -> None:
    print(message, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_train_messages(path: Path) -> list[dict]:
    return load_jsonl(path)


def main() -> int:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    log("NutriOffline Phase 4 dataset validation")

    for path in (RAW_GENERATED, TRAIN_JSONL, VAL_JSONL, STATS_JSON, MANUAL_REVIEW_SAMPLE):
        if not path.exists():
            log(f"FAIL: missing {path}")
            return 1

    raw = load_jsonl(RAW_GENERATED)
    train = load_train_messages(TRAIN_JSONL)
    val = load_train_messages(VAL_JSONL)
    stats = json.loads(STATS_JSON.read_text(encoding="utf-8"))

    if len(train) < MIN_TRAIN_EXAMPLES:
        log(f"FAIL: train count {len(train)} < {MIN_TRAIN_EXAMPLES}")
        return 1
    if len(val) < MIN_VAL_EXAMPLES:
        log(f"FAIL: val count {len(val)} < {MIN_VAL_EXAMPLES}")
        return 1

    passed, failed = validate_all(raw)
    if failed:
        log(f"FAIL: grounding validation — {len(failed)} failed examples")
        for item in failed[:3]:
            log(f"  - {item.get('example_id')}: {item.get('validation_errors')}")
        return 1

    log(f"PASS: grounding 100% ({len(passed)}/{len(raw)})")

    pt_ratio = stats.get("by_language", {}).get("pt", 0) / max(stats.get("total_examples", 1), 1)
    if pt_ratio < 0.90:
        log(f"WARN: PT-BR ratio {pt_ratio:.1%} below 90% target")
    else:
        log(f"PASS: PT-BR ratio {pt_ratio:.1%}")

    if not stats.get("fits_2048_context", False):
        log(f"FAIL: max token estimate {stats.get('max_tokens_estimate')} exceeds 2048")
        return 1
    log(f"PASS: max token estimate {stats.get('max_tokens_estimate')} <= 2048")

    categories = Counter()
    for example in raw:
        categories[example["generation_log"]["category"]] += 1
    log(f"PASS: categories — {dict(categories)}")

    log(f"PASS: train={len(train)} val={len(val)} total={len(raw)}")
    log("PASS: NutriOffline Phase 4 dataset gate (N-04)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
