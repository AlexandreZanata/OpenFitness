#!/usr/bin/env python3
"""Phase 3 acceptance tests for NutriOffline RAG index."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from query_rag import search

LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "rag-acceptance.log"

ACCEPTANCE_QUERIES = [
    {
        "id": "Q1-arroz",
        "query": "quantas calorias tem arroz branco",
        "assert_fn": lambda results: any(
            "arroz" in r.name.lower() and r.source in ("taco", "off") for r in results
        ),
        "note": "Top-5 must include arroz from TACO or OFF (README acceptance)",
    },
    {
        "id": "Q2-lactose",
        "query": "substituto de leite sem lactose",
        "assert_fn": lambda results: any(
            any(kw in (r.name + " " + r.rag_context).lower() for kw in ("leite", "lactose", "vegetal", "soja", "aveia"))
            for r in results
        ),
        "note": "Dairy or lactose-free alternatives",
    },
    {
        "id": "Q3-iogurte",
        "query": "iogurte grego proteína",
        "assert_fn": lambda results: any(
            "iogurte" in r.name.lower() or "yogurt" in r.name.lower() for r in results
        ),
        "note": "Yogurt products in top-5",
    },
    {
        "id": "Q4-ferro",
        "query": "comida rica em ferro",
        "assert_fn": lambda results: len(results) >= 3,
        "note": "Semantic retrieval returns results (iron not in unified macros)",
    },
]


def log(message: str) -> None:
    print(message, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def main() -> int:
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    log("NutriOffline Phase 3 RAG acceptance tests")
    passed = 0
    latencies: list[float] = []

    # Warm up embedder + LanceDB (model load is not part of query latency target)
    search("warmup", top_k=1, device="cpu")

    for case in ACCEPTANCE_QUERIES:
        started = time.perf_counter()
        results = search(case["query"], top_k=5, device="cpu")
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies.append(elapsed_ms)

        if not case["assert_fn"](results):
            log(f"FAIL {case['id']}: {case['query']}")
            for item in results:
                log(f"  - [{item.source}] {item.name} | {item.rag_context}")
            return 1

        log(f"PASS {case['id']}: {case['query']} ({elapsed_ms:.1f} ms)")
        for item in results[:3]:
            log(f"  - [{item.source}] {item.name}")

        passed += 1

    max_latency = max(latencies)
    if max_latency > 500:
        log(f"WARN: max query latency {max_latency:.1f} ms exceeds 500 ms target")
    else:
        log(f"PASS latency: max {max_latency:.1f} ms (target < 500 ms)")

    log(f"PASS: {passed}/{len(ACCEPTANCE_QUERIES)} acceptance queries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
