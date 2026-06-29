#!/usr/bin/env python3
"""API integration test — 20 natural-language food queries on mobile runtime."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR.parents[1] / "logs"

NL_FOOD_QUERIES = [
    "Quantas calorias tem 100g de arroz branco cozido?",
    "Quantas calorias tem 100g de banana prata?",
    "Quanto de proteína tem 100g de frango grelhado?",
    "Quanto de fibra tem feijão preto 80g?",
    "Quantas calorias tem 170g de iogurte vigor?",
    "Quantas calorias tem 100g de ovo cozido?",
    "Quantas calorias tem 100g de batata inglesa cozida?",
    "Quantas calorias tem 100g de maçã fuji?",
    "Quantas calorias tem 100g de aveia em flocos?",
    "Quantas calorias tem 100g de lentilha cozida?",
    "Quantas calorias tem 100g de mandioca cozida?",
    "Quantas calorias tem 100g de cenoura crua?",
    "Quantas calorias tem 100g de tomate?",
    "Quantas calorias tem 100g de melancia?",
    "Quantas calorias tem 100g de laranja pera?",
    "Quantas calorias tem 100g de mamão formosa?",
    "Quantas calorias tem 100g de brócolis cozido?",
    "Quantas calorias tem 100g de couve manteiga crua?",
    "Qual tem mais proteína: frango ou ovo?",
    "Existe opção mais leve que arroz?",
]


def post_chat(base_url: str, message: str, *, runtime: str = "mobile") -> dict:
    payload = json.dumps(
        {"message": message, "runtime": runtime, "use_rag": True, "top_k": 5},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/nutri/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def has_grounded_content(answer: str) -> bool:
    if "Não encontrado" in answer or "Não encontrei" in answer:
        return True
    if re.search(r"\d+\s*kcal", answer, re.I):
        return True
    if "|" in answer and "kcal" in answer.lower():
        return True
    if re.search(r"\d+[.,]?\d*\s*g", answer):
        return True
    if "proteína" in answer.lower() or "alternativa" in answer.lower():
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Mobile runtime API NL food test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8090")
    parser.add_argument("--runtime", default="mobile", choices=("mobile", "desktop"))
    args = parser.parse_args()

    health_url = f"{args.base_url.rstrip('/')}/v1/nutri/health?runtime={args.runtime}"
    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"ERROR: API not reachable at {args.base_url} — {exc}", file=sys.stderr)
        print("Start server: cd nutri-offline && python scripts/app/server.py", file=sys.stderr)
        return 1

    if args.runtime == "mobile" and not health.get("ready"):
        print("ERROR: mobile pack not ready — run build_pack.py", file=sys.stderr)
        return 1

    results: list[dict] = []
    failures = 0
    latencies: list[float] = []

    for query in NL_FOOD_QUERIES:
        started = time.perf_counter()
        try:
            data = post_chat(args.base_url, query, runtime=args.runtime)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"FAIL HTTP {exc.code}: {query}\n  {body}", file=sys.stderr)
            failures += 1
            results.append({"query": query, "ok": False, "error": body})
            continue

        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies.append(elapsed_ms)
        ok = (
            data.get("runtime") == args.runtime
            and data.get("mode") in {"lookup", "compare", "substitute", "clarify", "llm"}
            and bool(data.get("answer"))
            and has_grounded_content(data["answer"])
        )
        if not ok:
            failures += 1
        results.append(
            {
                "query": query,
                "ok": ok,
                "mode": data.get("mode"),
                "latency_ms": round(data.get("latency_ms", elapsed_ms), 1),
                "sources": len(data.get("sources") or []),
                "answer_preview": (data.get("answer") or "")[:120],
            }
        )
        status = "OK" if ok else "FAIL"
        print(f"{status} [{data.get('mode')}] {elapsed_ms:.0f}ms — {query}")

    report = {
        "runtime": args.runtime,
        "base_url": args.base_url,
        "total": len(NL_FOOD_QUERIES),
        "passed": len(NL_FOOD_QUERIES) - failures,
        "failed": failures,
        "latency_ms_median": round(sorted(latencies)[len(latencies) // 2], 1) if latencies else 0,
        "results": results,
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / "mobile-chat-api-nl-test.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nPassed {report['passed']}/{report['total']} — log: {out}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
