#!/usr/bin/env python3
"""Phase 7 offline acceptance tests — 5 scenarios from README."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_paths import LOG_DIR
from orchestrator import NutriAssistant

LOG_DIR.mkdir(parents=True, exist_ok=True)

# TACO golden: Arroz, tipo 1, cozido ~128 kcal per 100g (Phase 2)
TACO_ARROZ_KCAL = 128
TOLERANCE_PCT = 2.0

SCENARIOS = [
    {
        "id": "S1-taco-calories",
        "question": "Quantas calorias tem Arroz, tipo 1, cozido por 100g segundo a TACO?",
        "note": "TACO arroz kcal from RAG context cited in answer",
    },
    {
        "id": "S2-compare",
        "question": "Qual tem mais proteína por 100g: frango grelhado ou ovo cozido?",
        "note": "Comparison using RAG context values",
    },
    {
        "id": "S3-off-branded",
        "question": "Informações nutricionais do iogurte grego Vigor",
        "note": "Branded OFF product with source citation",
    },
    {
        "id": "S4-unknown",
        "question": "Quantas calorias tem o alimento fictício NutriXYZ-404 por 100g?",
        "note": "Unknown food — no invented precise macros",
    },
    {
        "id": "S5-session",
        "question": "Quantas calorias tem banana prata crua por 100g?",
        "note": "Follow-up query in offline session (banana ~98 kcal TACO)",
    },
]


def log(message: str) -> None:
    print(message, flush=True)


def within_tolerance(actual: float, expected: float, tolerance_pct: float = TOLERANCE_PCT) -> bool:
    if expected == 0:
        return abs(actual - expected) <= 1
    return abs(actual - expected) / abs(expected) * 100 <= tolerance_pct


def extract_kcals(text: str) -> list[int]:
    return [int(round(float(m))) for m in re.findall(r"(\d+(?:\.\d+)?)\s*kcal", text, re.I)]


def extract_context_kcals(context: str) -> list[int]:
    return extract_kcals(context)


def assert_s1(result) -> list[str]:
    errors: list[str] = []
    if not result.rag_context_used:
        errors.append("RAG not used")
    context_kcals = extract_context_kcals(result.rag_context)
    answer_kcals = extract_kcals(result.answer)
    taco_in_context = any(
        "taco" in line.lower() and "arroz" in line.lower()
        for line in result.rag_context.splitlines()
    ) or any(s.get("source") == "taco" for s in result.sources)
    if not taco_in_context and not any(k in range(120, 136) for k in context_kcals):
        errors.append("TACO arroz not in RAG top results")
    if answer_kcals:
        if context_kcals and not any(
            within_tolerance(a, c, 5.0) for a in answer_kcals for c in context_kcals
        ):
            errors.append(f"answer kcal {answer_kcals} not aligned with context {context_kcals[:5]}")
    elif "128" not in result.answer and "kcal" not in result.answer.lower():
        errors.append("no kcal in answer")
    if "taco" not in result.answer.lower():
        errors.append("missing TACO citation")
    return errors


def assert_s2(result) -> list[str]:
    errors: list[str] = []
    if not result.rag_context_used:
        errors.append("RAG not used")
    text = result.answer.lower()
    if not any(kw in text for kw in ("prote", "frango", "ovo")):
        errors.append("comparison answer lacks expected terms")
    return errors


def assert_s3(result) -> list[str]:
    errors: list[str] = []
    if not result.rag_context_used:
        errors.append("RAG not used")
    if not any(s.get("source") == "off" for s in result.sources):
        if "open food facts" not in result.answer.lower() and "off" not in result.answer.lower():
            errors.append("OFF source not cited")
    if "iogurte" not in result.answer.lower() and "yogurt" not in result.answer.lower():
        errors.append("yogurt product not mentioned")
    return errors


def assert_s4(result) -> list[str]:
    errors: list[str] = []
    if re.search(r"NutriXYZ-404.*\d{2,}\s*kcal", result.answer, re.I):
        errors.append("invented precise kcal for unknown food")
    if re.search(r"\d{3}\s*kcal", result.answer) and "nutrixyz" in result.answer.lower():
        errors.append("hallucinated kcal for fabricated food")
    return errors


def assert_s5(result) -> list[str]:
    errors: list[str] = []
    if not result.rag_context_used:
        errors.append("RAG not used")
    if "kcal" not in result.answer.lower() and "calor" not in result.answer.lower():
        errors.append("no calorie mention for banana")
    return errors


ASSERTIONS = {
    "S1-taco-calories": assert_s1,
    "S2-compare": assert_s2,
    "S3-off-branded": assert_s3,
    "S4-unknown": assert_s4,
    "S5-session": assert_s5,
}


def install_offline_guard() -> list[str]:
    """Block outbound HTTP except localhost; returns mutable violation log."""
    violations: list[str] = []
    original_urlopen = urllib.request.urlopen

    def guarded_urlopen(url, *args, **kwargs):
        url_str = url if isinstance(url, str) else url.full_url
        if not any(host in url_str for host in ("127.0.0.1", "localhost")):
            violations.append(url_str)
            raise urllib.error.URLError("external network blocked for offline test")
        return original_urlopen(url, *args, **kwargs)

    urllib.request.urlopen = guarded_urlopen  # type: ignore[method-assign]
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-guard", action="store_true", default=True)
    args = parser.parse_args()

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = LOG_DIR / f"e2e-offline-{timestamp}.json"
    report: dict = {"timestamp": timestamp, "scenarios": [], "passed": 0, "failed": 0}

    log("NutriOffline Phase 7 E2E offline acceptance tests")

    assistant = NutriAssistant()
    health = assistant.health()
    if not health.get("llm_server"):
        log("FAIL: llama-server not reachable — run start_offline.sh first")
        return 1
    log(f"Health: {health}")

    network_errors: list[str] = []
    if args.offline_guard:
        network_errors = install_offline_guard()

    for scenario in SCENARIOS:
        started = time.perf_counter()
        result = assistant.ask(scenario["question"], debug=True)
        elapsed = (time.perf_counter() - started) * 1000

        assert_fn = ASSERTIONS[scenario["id"]]
        errors = assert_fn(result)

        entry = {
            "id": scenario["id"],
            "question": scenario["question"],
            "note": scenario["note"],
            "passed": not errors,
            "errors": errors,
            "latency_ms": round(elapsed, 1),
            "answer_preview": result.answer[:300],
            "sources": result.sources,
        }
        report["scenarios"].append(entry)

        if errors:
            report["failed"] += 1
            log(f"FAIL {scenario['id']}: {errors}")
            log(f"  Answer: {result.answer[:200]}...")
        else:
            report["passed"] += 1
            log(f"PASS {scenario['id']}: {scenario['note']} ({elapsed:.0f} ms)")

    report["offline_guard"] = not network_errors
    report["network_violations"] = network_errors

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"Report: {report_path}")

    total = len(SCENARIOS)
    if report["passed"] == total:
        log(f"PASS: {total}/{total} offline acceptance scenarios")
        return 0

    log(f"FAIL: {report['passed']}/{total} scenarios passed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
