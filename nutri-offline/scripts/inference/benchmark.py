#!/usr/bin/env python3
"""Benchmark llama-server latency (Phase 6 N-06-08)."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inference_paths import BENCHMARK_LOG, INFERENCE_URL
from rag_prompt import build_messages_with_rag
from test_inference import chat_completion, wait_for_server


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-server", action="store_true")
    args = parser.parse_args()

    if args.wait_server and not wait_for_server():
        print("FAIL: server not ready", flush=True)
        return 1

    results: dict = {"context_sizes": [], "runs": []}

    prompts = [
        [{"role": "user", "content": "Olá"}],
        [{"role": "user", "content": "Explique proteínas em uma frase."}],
        build_messages_with_rag("quantas calorias tem arroz branco", top_k=5),
    ]

    for index, messages in enumerate(prompts):
        label = ["short", "medium", "rag"][index]
        _, latency = chat_completion(messages, max_tokens=128)
        results["runs"].append({"label": label, "latency_ms": round(latency, 1)})

    results["max_latency_ms"] = max(r["latency_ms"] for r in results["runs"])
    results["recorded_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    BENCHMARK_LOG.parent.mkdir(parents=True, exist_ok=True)
    BENCHMARK_LOG.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
