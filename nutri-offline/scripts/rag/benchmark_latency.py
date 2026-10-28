#!/usr/bin/env python3
"""G-PERF hybrid search latency benchmark — Phase 11 (N-11-13)."""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
RAG_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(RAG_DIR))

from _paths import LOG_DIR
from index_catalog import index_snapshot, load_index_metadata
from rag_pipeline import RagPipeline

SAMPLE_QUERIES = [
    "arroz 100g",
    "banana prata",
    "frango grelhado 100g",
    "feijão preto",
    "iogurte vigor",
    "queijo minas",
    "batata doce cozida",
    "macarrão cozido",
    "ovo cozido",
    "leite integral",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Hybrid search latency benchmark")
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=110629)
    parser.add_argument("--p95-max-ms", type=float, default=300.0)
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()

    rag = RagPipeline.get()
    rng = random.Random(args.seed)
    queries = [rng.choice(SAMPLE_QUERIES) for _ in range(args.samples)]

    latencies: list[float] = []
    for query in queries:
        started = time.perf_counter()
        rag.search_for_lookup(query, top_k=5)
        latencies.append((time.perf_counter() - started) * 1000)

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    meta = load_index_metadata()
    index = index_snapshot()

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "timestamp": timestamp,
        "samples": args.samples,
        "index_scope": meta.get("scope"),
        "index_records": index.record_count if index else 0,
        "index_size_mb": index.index_size_mb if index else None,
        "latency_ms_p50": round(p50, 2),
        "latency_ms_p95": round(p95, 2),
        "p95_target_ms": args.p95_max_ms,
        "pass": p95 <= args.p95_max_ms,
    }
    out = LOG_DIR / f"latency-benchmark-{timestamp}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"p50={p50:.1f}ms p95={p95:.1f}ms (target p95<{args.p95_max_ms}ms)")
    print(f"Report: {out}")
    status = "PASS" if report["pass"] else "FAIL"
    print(f"{status}: G-PERF latency benchmark")

    if args.gate and not report["pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
