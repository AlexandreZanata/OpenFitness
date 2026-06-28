#!/usr/bin/env python3
"""RAG V2 end-to-end latency benchmark (RAG-V2-13)."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_paths import LOG_DIR
from orchestrator import NutriAssistant

# Pre-RAG-V2 shorthand p95 from 2026-06-28 logs (README-RAG-V2)
BASELINE_LOOKUP_P95_MS = 12_000.0

LOOKUP_QUERIES = [
    "arroz 100g",
    "banana 100g",
    "arroz 100g, carne 200g",
    "feijão 80g",
    "iogurte vigor 170g",
]

REASONING_QUERIES = [
    "Quantas calorias tem 100g de arroz branco cozido?",
    "Qual tem mais proteína por 100g: frango grelhado ou ovo cozido?",
]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((pct / 100) * (len(ordered) - 1)))
    return ordered[index]


def _summarize(values: list[float]) -> dict[str, float]:
    return {
        "mean": round(statistics.mean(values), 1),
        "p50": round(_percentile(values, 50), 1),
        "p95": round(_percentile(values, 95), 1),
        "min": round(min(values), 1),
        "max": round(max(values), 1),
    }


def run_benchmark(*, repeats: int, skip_llm: bool) -> dict:
    assistant = NutriAssistant()
    lookup_latencies: list[float] = []
    reasoning_latencies: list[float] = []
    samples: list[dict] = []

    for _ in range(repeats):
        for query in LOOKUP_QUERIES:
            started = time.perf_counter()
            result = assistant.ask(query, mode="auto")
            elapsed = (time.perf_counter() - started) * 1000
            lookup_latencies.append(elapsed)
            samples.append(
                {
                    "query": query,
                    "mode": result.mode,
                    "latency_ms": round(elapsed, 1),
                    "cached": result.debug.get("cache_hit", False),
                }
            )

    if not skip_llm:
        for query in REASONING_QUERIES:
            started = time.perf_counter()
            result = assistant.ask(query, mode="auto")
            elapsed = (time.perf_counter() - started) * 1000
            reasoning_latencies.append(elapsed)
            samples.append(
                {
                    "query": query,
                    "mode": result.mode,
                    "latency_ms": round(elapsed, 1),
                    "cached": result.debug.get("cache_hit", False),
                }
            )

    lookup_summary = _summarize(lookup_latencies)
    report: dict = {
        "recorded_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "lookup": lookup_summary,
        "baseline_lookup_p95_ms": BASELINE_LOOKUP_P95_MS,
        "lookup_speedup_vs_baseline_p95": round(
            BASELINE_LOOKUP_P95_MS / lookup_summary["p95"], 2
        )
        if lookup_summary["p95"] > 0
        else None,
        "lookup_target_p95_ms": 800,
        "lookup_target_met": lookup_summary["p95"] <= 800,
        "cache": assistant.cache_stats(),
        "samples": samples,
    }

    if reasoning_latencies:
        reasoning_summary = _summarize(reasoning_latencies)
        report["reasoning"] = reasoning_summary
        report["reasoning_target_p95_ms"] = 3000
        report["reasoning_target_met"] = reasoning_summary["p95"] <= 3000

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline RAG V2 benchmark")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--skip-llm", action="store_true", help="Skip reasoning queries")
    parser.add_argument("--json-out", type=Path, default=LOG_DIR / "rag-v2-benchmark.json")
    args = parser.parse_args()

    report = run_benchmark(repeats=args.repeats, skip_llm=args.skip_llm)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

    if not report["lookup_target_met"]:
        print(
            f"WARN: lookup p95 {report['lookup']['p95']} ms exceeds target 800 ms",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
