#!/usr/bin/env python3
"""Manual API parity — admin chat must match mobile modes for shared NL queries."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR.parents[1] / "logs"

PARITY_QUERIES = [
    ("lookup", "Quantas calorias tem 100g de arroz branco cozido?"),
    ("lookup", "Quantas calorias tem 100g de banana prata?"),
    ("compare", "Qual tem mais proteína: frango ou ovo?"),
    ("substitute", "Existe opção mais leve que arroz?"),
    ("lookup", "arroz 100g, feijão 80g"),
]


def post_chat(base_url: str, message: str, *, runtime: str) -> dict:
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
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Admin ↔ mobile API mode parity")
    parser.add_argument("--base-url", default="http://127.0.0.1:8090")
    args = parser.parse_args()

    results: list[dict] = []
    failures = 0

    for expected_mode, query in PARITY_QUERIES:
        row: dict = {"query": query, "expected_mode": expected_mode}
        try:
            mobile = post_chat(args.base_url, query, runtime="mobile")
            desktop = post_chat(args.base_url, query, runtime="desktop")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"FAIL HTTP {exc.code}: {query}\n  {body}", file=sys.stderr)
            failures += 1
            row["error"] = body
            results.append(row)
            continue
        except urllib.error.URLError as exc:
            print(f"ERROR: API not reachable — {exc}", file=sys.stderr)
            return 1

        mobile_mode = mobile.get("mode")
        desktop_mode = desktop.get("mode")
        ok = (
            mobile_mode == expected_mode
            and desktop_mode == expected_mode
            and mobile.get("runtime") == "mobile"
            and desktop.get("runtime") == "desktop"
        )
        if not ok:
            failures += 1
        row.update(
            {
                "ok": ok,
                "mobile_mode": mobile_mode,
                "desktop_mode": desktop_mode,
            }
        )
        results.append(row)
        status = "OK" if ok else "FAIL"
        print(f"{status} expected={expected_mode} mobile={mobile_mode} desktop={desktop_mode} — {query}")

    report = {
        "base_url": args.base_url,
        "total": len(PARITY_QUERIES),
        "passed": len(PARITY_QUERIES) - failures,
        "failed": failures,
        "results": results,
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / "admin-mobile-parity.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nPassed {report['passed']}/{report['total']} — log: {out}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
