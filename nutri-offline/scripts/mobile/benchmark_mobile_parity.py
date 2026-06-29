#!/usr/bin/env python3
"""Parity benchmark — mobile vs desktop lookup path (N-08-19)."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from statistics import median

APP_DIR = Path(__file__).resolve().parents[1] / "app"
MOBILE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from mobile_assistant import MobileNutriAssistant  # noqa: E402
from orchestrator import NutriAssistant  # noqa: E402

from mobile_paths import LOG_DIR, VECTORS_DB  # noqa: E402

GOLDEN_LOOKUP = [
    "arroz 100g",
    "banana 100g",
    "arroz 100g, feijão 100g",
    "nutrixyz 100g",
    "iogurte vigor 170g",
]

NL_PARITY = [
    "Quantas calorias tem 100g de arroz branco cozido?",
    "Quantas calorias tem 100g de banana?",
    "calorias arroz 100g",
    "Quanto de proteína tem 100g de frango grelhado?",
    "Quanto de fibra tem feijão 80g?",
    "Quantas calorias tem 170g de iogurte vigor?",
    "Quantas calorias tem 100g de arroz?",
    "Quantas calorias tem 100g de feijão preto cozido?",
    "Quantas calorias tem 100g de ovo cozido?",
    "Quantas calorias tem 100g de batata cozida?",
    "Quantas calorias tem 100g de maçã?",
    "Quantas calorias tem 100g de aveia?",
    "Quantas calorias tem 100g de lentilha cozida?",
    "Quantas calorias tem 100g de mandioca cozida?",
    "Quantas calorias tem 100g de feijão carioca cozido?",
    "Quantas calorias tem 100g de cenoura crua?",
    "Quantas calorias tem 100g de tomate?",
    "Quantas calorias tem 100g de melancia?",
    "Quantas calorias tem 100g de laranja?",
    "Quantas calorias tem 100g de mamão?",
]


def extract_table_kcal(answer: str) -> list[int]:
    rows = [line for line in answer.split("\n") if line.startswith("|") and "kcal" not in line.lower()]
    values: list[int] = []
    for row in rows:
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if len(cells) >= 4 and cells[0] not in {"**Total**", "Alimento"}:
            kcal_cell = cells[3]
            if kcal_cell.replace(".", "").isdigit():
                values.append(int(float(kcal_cell)))
    return values


def extract_table_macros(answer: str) -> dict[str, list[float]]:
    rows = [line for line in answer.split("\n") if line.startswith("|") and "kcal" not in line.lower()]
    values: dict[str, list[float]] = {"kcal": [], "protein": [], "carbs": [], "fat": []}
    for row in rows:
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if len(cells) >= 7 and cells[0] not in {"**Total**", "Alimento"}:
            for idx, key in enumerate(["kcal", "protein", "carbs", "fat"], start=3):
                cell = cells[idx].replace("g", "").replace("—", "").strip()
                if cell and cell.replace(".", "").isdigit():
                    values[key].append(float(cell))
    return values


def extract_prose_kcal(answer: str) -> int | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*kcal", answer.lower())
    return int(round(float(match.group(1)))) if match else None


def within_tolerance(actual: float, expected: float, pct: float = 2.0) -> bool:
    if expected == 0:
        return abs(actual) <= 1
    return abs(actual - expected) / abs(expected) * 100 <= pct


def macros_match(
    desktop_answer: str,
    mobile_answer: str,
    *,
    desktop_sources: list[dict] | None = None,
    mobile_sources: list[dict] | None = None,
    tolerance_pct: float = 2.0,
) -> bool:
    if desktop_sources and mobile_sources:
        desktop_ids = {item.get("id") for item in desktop_sources if item.get("id")}
        mobile_ids = {item.get("id") for item in mobile_sources if item.get("id")}
        if desktop_ids & mobile_ids:
            return True

    d = extract_table_macros(desktop_answer)
    m = extract_table_macros(mobile_answer)
    for key in ("kcal", "protein", "carbs", "fat"):
        if d[key] and m[key]:
            return any(
                within_tolerance(a, b, tolerance_pct)
                for a in m[key]
                for b in d[key]
            )
    d_kcal = extract_prose_kcal(desktop_answer)
    m_kcal = extract_prose_kcal(mobile_answer)
    if d_kcal is not None and m_kcal is not None:
        return within_tolerance(m_kcal, d_kcal, tolerance_pct)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Mobile parity benchmark")
    args = parser.parse_args()

    if not VECTORS_DB.is_file():
        print("ERROR: mobile index not built", file=sys.stderr)
        return 1

    desktop = NutriAssistant()
    mobile = MobileNutriAssistant()

    golden_results = []
    for query in GOLDEN_LOOKUP:
        d = desktop.ask(query, mode="lookup")
        m = mobile.ask(query)
        golden_results.append(
            {
                "query": query,
                "desktop_kcal": extract_table_kcal(d.answer),
                "mobile_kcal": extract_table_kcal(m.answer),
                "match": extract_table_kcal(d.answer) == extract_table_kcal(m.answer),
            }
        )

    nl_results = []
    latencies: list[float] = []
    for query in NL_PARITY:
        d = desktop.ask(query, mode="lookup")
        m = mobile.ask(query)
        latencies.append(m.latency_ms)
        nl_results.append(
            {
                "query": query,
                "match": macros_match(
                    d.answer,
                    m.answer,
                    desktop_sources=d.sources,
                    mobile_sources=m.sources,
                ),
                "desktop_mode": d.mode,
                "mobile_mode": m.mode,
            }
        )

    nl_accuracy = sum(1 for row in nl_results if row["match"]) / len(nl_results)
    latencies_sorted = sorted(latencies)
    p95 = latencies_sorted[int(max(0, len(latencies_sorted) * 0.95 - 1))]

    report = {
        "golden_g1_g5": golden_results,
        "golden_pass": all(row["match"] for row in golden_results),
        "nl_parity": nl_results,
        "nl_accuracy": round(nl_accuracy, 4),
        "latency_ms_p95": round(p95, 1),
        "latency_ms_median": round(median(latencies), 1),
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    output = LOG_DIR / "mobile-parity-benchmark.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["golden_pass"] and nl_accuracy >= 0.95 else 1


if __name__ == "__main__":
    raise SystemExit(main())
