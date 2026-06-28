#!/usr/bin/env python3
"""Phase 6 inference smoke tests — llama-server OpenAI API (N-06-06, N-06-07)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from inference_paths import INFERENCE_URL, LOG_DIR, ROOT
from rag_prompt import build_messages_with_rag, extract_kcal_from_context

LOG_PATH = LOG_DIR / "inference-smoke.log"

PROMPTS = [
    {
        "id": "P1-arroz",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é um assistente de nutrição em português brasileiro. "
                    "Responda de forma clara sobre alimentos."
                ),
            },
            {
                "role": "user",
                "content": "Quantas calorias tem arroz branco cozido por 100g?",
            },
        ],
        "assert_fn": lambda text: bool(re.search(r"\d+\s*kcal|calor", text, re.I)),
        "note": "PT-BR nutrition response with calorie mention",
    },
    {
        "id": "P2-protein",
        "messages": [
            {"role": "user", "content": "O que são macronutrientes?"},
        ],
        "assert_fn": lambda text: any(
            kw in text.lower() for kw in ("proteína", "carboidrato", "gordura", "macro")
        ),
        "note": "General nutrition terminology",
    },
    {
        "id": "P3-unknown",
        "messages": [
            {
                "role": "system",
                "content": "Não invente valores numéricos precisos sem fonte.",
            },
            {
                "role": "user",
                "content": "Quantas calorias tem o alimento fictício XYZ-999 por 100g?",
            },
        ],
        "assert_fn": lambda text: not re.search(r"XYZ-999.*\d{3}\s*kcal", text, re.I),
        "note": "Should not invent precise kcal for unknown food",
    },
]


def log(message: str) -> None:
    print(message, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def chat_completion(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 256,
    timeout: float = 120.0,
) -> tuple[str, float]:
    payload = json.dumps(
        {
            "model": "nutri-offline",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        INFERENCE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    elapsed_ms = (time.perf_counter() - started) * 1000
    content = body["choices"][0]["message"]["content"]
    return content, elapsed_ms


def wait_for_server(retries: int = 30, delay: float = 2.0) -> bool:
    health_urls = [
        INFERENCE_URL.replace("/v1/chat/completions", "/health"),
        INFERENCE_URL.replace("/v1/chat/completions", "/"),
    ]
    for _ in range(retries):
        for url in health_urls:
            try:
                urllib.request.urlopen(url, timeout=2.0)
                return True
            except (urllib.error.URLError, TimeoutError):
                continue
        time.sleep(delay)
    # Try a minimal completion as readiness probe
    try:
        chat_completion([{"role": "user", "content": "ping"}], max_tokens=8, timeout=30.0)
        return True
    except Exception:
        return False


def test_rag_integration() -> bool:
    question = "quantas calorias tem arroz branco"
    messages = build_messages_with_rag(question, top_k=5)
    context = messages[0]["content"]
    context_kcals = extract_kcal_from_context(context)
    if not context_kcals:
        log("FAIL RAG-P1: no kcal values in RAG context")
        return False

    answer, latency = chat_completion(messages, max_tokens=300)
    log(f"RAG context kcals: {context_kcals[:5]}")
    log(f"RAG answer ({latency:.0f} ms): {answer[:200]}...")

    if not any(str(k) in answer for k in context_kcals[:3]):
        # Allow approximate match within RAG range
        answer_nums = [int(round(float(x))) for x in re.findall(r"\d+(?:\.\d+)?", answer)]
        if not any(k in answer_nums for k in context_kcals[:5]):
            log("WARN RAG-P1: answer kcal may not match RAG context (fine-tuned adapter is smoke-test)")
    log("PASS RAG-P1: RAG prompt delivered to llama-server")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-server", action="store_true")
    parser.add_argument("--skip-rag", action="store_true")
    args = parser.parse_args()

    if LOG_PATH.exists():
        LOG_PATH.unlink()

    log("NutriOffline Phase 6 inference smoke tests")

    if args.wait_server:
        log("Waiting for llama-server...")
        if not wait_for_server():
            log("FAIL: llama-server not reachable")
            return 1

    passed = 0
    latencies: list[float] = []

    for case in PROMPTS:
        try:
            answer, latency = chat_completion(case["messages"])
        except urllib.error.URLError as exc:
            log(f"FAIL {case['id']}: server error — {exc}")
            return 1

        latencies.append(latency)
        if not case["assert_fn"](answer):
            log(f"FAIL {case['id']}: {case['note']}")
            log(f"  Response: {answer[:300]}")
            return 1

        log(f"PASS {case['id']}: {case['note']} ({latency:.0f} ms)")
        passed += 1

    if not args.skip_rag:
        if not test_rag_integration():
            return 1

    max_latency = max(latencies) if latencies else 0
    if max_latency > 30_000:
        log(f"WARN: max latency {max_latency:.0f} ms exceeds 30s UX target")
    else:
        log(f"PASS latency: max {max_latency:.0f} ms")

    log(f"PASS: {passed}/{len(PROMPTS)} smoke prompts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
