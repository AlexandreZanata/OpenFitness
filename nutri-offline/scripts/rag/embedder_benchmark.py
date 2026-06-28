#!/usr/bin/env python3
"""Compare embedding model latency for RAG V2 (RAG-V2-14)."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import EMBEDDER_CANDIDATES, LOG_DIR
from embed import encode_texts, load_embedder, reset_embedder_cache, resolve_device

GOLDEN_QUERIES = [
    "arroz 100g",
    "banana 100g",
    "feijão carioca cozido",
    "carne bovina grelhada",
    "iogurte grego",
    "quantas calorias tem arroz branco",
    "frango grelhado proteína",
    "ovo cozido",
    "arroz integral",
    "batata doce assada",
]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((pct / 100) * (len(ordered) - 1)))
    return ordered[index]


def benchmark_model(model_name: str, *, device: str, runs: int) -> dict:
    reset_embedder_cache()
    model = load_embedder(device, model_name=model_name)

    # Warmup
    encode_texts(model, [GOLDEN_QUERIES[0]], show_progress=False)

    latencies_ms: list[float] = []
    for _ in range(runs):
        for query in GOLDEN_QUERIES:
            started = time.perf_counter()
            encode_texts(model, [query], show_progress=False)
            latencies_ms.append((time.perf_counter() - started) * 1000)

    return {
        "model": model_name,
        "dims": EMBEDDER_CANDIDATES.get(model_name),
        "device": device,
        "queries": len(GOLDEN_QUERIES),
        "runs": runs,
        "latency_ms": {
            "mean": round(statistics.mean(latencies_ms), 2),
            "p50": round(_percentile(latencies_ms, 50), 2),
            "p95": round(_percentile(latencies_ms, 95), 2),
        },
        "note": (
            "Index rebuild required when switching to a model with different embedding dimensions."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Embedder A/B latency benchmark")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument(
        "--models",
        nargs="*",
        default=list(EMBEDDER_CANDIDATES.keys()),
        help="Embedding models to compare",
    )
    parser.add_argument("--json-out", type=Path, default=LOG_DIR / "embedder-ab-benchmark.json")
    args = parser.parse_args()

    device = resolve_device(args.device)
    results = [benchmark_model(name, device=device, runs=args.runs) for name in args.models]

    baseline = results[0]["latency_ms"]["p95"] if results else 0.0
    for item in results[1:]:
        if baseline > 0:
            item["speedup_vs_baseline_p95"] = round(baseline / item["latency_ms"]["p95"], 2)

    payload = {
        "recorded_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "baseline_model": results[0]["model"] if results else None,
        "results": results,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
