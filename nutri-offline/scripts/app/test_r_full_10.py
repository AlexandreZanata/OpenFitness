#!/usr/bin/env python3
"""R-FULL-10 desktop smoke — Phase 11 regression set."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from orchestrator import NutriAssistant  # noqa: E402

RAG_DIR = APP_DIR.parent / "rag"
sys.path.insert(0, str(RAG_DIR))

from index_catalog import index_snapshot  # noqa: E402

LOG_DIR = APP_DIR.parents[1] / "logs"

RFULL10 = [
    ("RF01", "arroz 100g", "lookup", lambda r: r.mode == "lookup" and any(s.get("source") == "taco" for s in r.sources)),
    ("RF02", "iogurte vigor 170g", "lookup", lambda r: r.mode == "lookup" and any(s.get("source") == "off" for s in r.sources)),
    ("RF03", "cheerios", "lookup", lambda r: r.mode in {"lookup", "llm"} and (any(s.get("source") == "fdc" for s in r.sources) or "cheerios" in r.answer.lower())),
    ("RF04", "mcdonald's big mac", "lookup", lambda r: r.mode in {"lookup", "llm"}),
    ("RF05", "100g frango grelhado", "lookup", lambda r: r.mode == "lookup" and any("410" in s.get("id", "") or "frango" in s.get("name", "").lower() for s in r.sources)),
    ("RF06", "nutrizxyabc 100g", "lookup", lambda r: "Não encontrado" in r.answer or "Não encontrei" in r.answer),
    ("RF07", "barcode 7891000100103", "lookup", lambda r: r.mode == "lookup"),
    ("RF08", "Qual tem mais proteína: arroz ou feijão?", "compare", lambda r: r.mode == "compare"),
    ("RF09", "Existe opção mais leve que arroz?", "substitute", lambda r: r.mode == "substitute"),
    ("RF10", "quantas calorias tem uma banana", "lookup", lambda r: r.mode == "lookup" and "kcal" in r.answer.lower()),
]

BRANDED_ONLY = {"RF03", "RF04"}


def main() -> int:
    parser = argparse.ArgumentParser(description="R-FULL-10 desktop smoke")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    index = index_snapshot()
    scope = index.scope if index else "v1"
    assistant = NutriAssistant()

    results: list[dict] = []
    failures = 0
    skipped = 0

    for case_id, query, expected_mode, predicate in RFULL10:
        if case_id in BRANDED_ONLY and scope != "all":
            results.append({"id": case_id, "skipped": True, "reason": "requires scope=all FDC branded index"})
            skipped += 1
            print(f"SKIP {case_id} (scope={scope}) — {query}")
            continue

        result = assistant.ask(query)
        ok = result.mode == expected_mode and predicate(result)
        if not ok:
            failures += 1
        results.append(
            {
                "id": case_id,
                "query": query,
                "expected_mode": expected_mode,
                "mode": result.mode,
                "ok": ok,
                "answer_preview": result.answer[:120],
            }
        )
        status = "OK" if ok else "FAIL"
        print(f"{status} {case_id} [{result.mode}] — {query}")

    report = {
        "index_scope": scope,
        "total": len(RFULL10),
        "passed": len(RFULL10) - failures - skipped,
        "failed": failures,
        "skipped": skipped,
        "results": results,
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = LOG_DIR / "r-full-10-smoke.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\nPassed {report['passed']}/{report['total']} (skipped {skipped}) — log: {out}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
