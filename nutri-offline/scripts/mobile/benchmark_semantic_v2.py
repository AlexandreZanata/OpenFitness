#!/usr/bin/env python3
"""Semantic engine v2 latency benchmark — p95 gate (Phase 9 exit criterion)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import median

APP_DIR = Path(__file__).resolve().parents[1] / "app"
MOBILE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from mobile_assistant import MobileNutriAssistant  # noqa: E402
from mobile_paths import LOG_DIR, VECTORS_DB  # noqa: E402

LATENCY_P95_TARGET_MS = 500.0
WARMUP_QUERY = "arroz 100g"

BASELINE_QUERIES = [
    "arroz 100g",
    "banana 100g",
    "100g de arror",
    "Quantas calorias tem 100g de arroz branco cozido?",
    "Quantas calorias tem 100g de banana?",
]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(max(0, len(ordered) * pct / 100 - 1))
    return ordered[index]


def load_semantic_v2_queries(fixture_path: Path) -> list[str]:
    if not fixture_path.is_file():
        return []
    queries: list[str] = []
    for line in fixture_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        queries.append(json.loads(line)["query"])
    return queries


def run_benchmark(*, repeats: int = 1) -> dict:
    assistant = MobileNutriAssistant()
    assistant.ask(WARMUP_QUERY)

    fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "semantic_v2_golden.jsonl"
    queries = list(dict.fromkeys(load_semantic_v2_queries(fixture) + BASELINE_QUERIES))

    per_query: list[dict] = []
    latencies: list[float] = []
    for query in queries:
        samples: list[float] = []
        for _ in range(repeats):
            started = time.perf_counter()
            result = assistant.ask(query)
            elapsed_ms = (time.perf_counter() - started) * 1000
            samples.append(elapsed_ms)
            latencies.append(elapsed_ms)
            if result.mode != "lookup" and query in BASELINE_QUERIES[:2]:
                raise RuntimeError(f"expected lookup for baseline query: {query}")
        per_query.append(
            {
                "query": query,
                "latency_ms_median": round(median(samples), 1),
                "mode": result.mode,
            }
        )

    p95 = _percentile(latencies, 95)
    return {
        "query_count": len(queries),
        "sample_count": len(latencies),
        "latency_ms_p95": round(p95, 1),
        "latency_ms_median": round(median(latencies), 1),
        "latency_ms_max": round(max(latencies), 1),
        "target_p95_ms": LATENCY_P95_TARGET_MS,
        "target_met": p95 <= LATENCY_P95_TARGET_MS,
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Semantic v2 mobile latency benchmark")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not VECTORS_DB.is_file():
        print("ERROR: mobile vectors.db missing — build mobile index first", file=sys.stderr)
        return 1

    report = run_benchmark(repeats=max(1, args.repeats))
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    output = LOG_DIR / "semantic-v2-benchmark.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))

    if not report["target_met"]:
        print(
            f"FAIL: p95 {report['latency_ms_p95']} ms exceeds target {LATENCY_P95_TARGET_MS} ms",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
