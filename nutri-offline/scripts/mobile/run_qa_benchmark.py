#!/usr/bin/env python3
"""Mobile QA benchmark runner — R10 regression + B20 full set (Phase 10)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
MOBILE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from mobile_assistant import MobileNutriAssistant  # noqa: E402
from mobile_paths import LOG_DIR, VECTORS_DB  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "mobile_qa_b20.jsonl"
DEFAULT_TOLERANCE_PCT = 5.0


@dataclass
class RowScore:
    row_id: str
    question: str
    status: str
    detail: str


def within_tolerance(actual: float, expected: float, tolerance_pct: float) -> bool:
    if expected == 0:
        return abs(actual) <= 1
    return abs(actual - expected) / abs(expected) * 100 <= tolerance_pct


def extract_table_kcal(answer: str) -> list[float]:
    rows = [line for line in answer.split("\n") if line.startswith("|") and "kcal" not in line.lower()]
    values: list[float] = []
    for row in rows:
        cells = [cell.strip() for cell in row.split("|") if cell.strip()]
        if len(cells) >= 4 and cells[0] not in {"**Total**", "Alimento"}:
            try:
                values.append(float(cells[3].replace(",", ".")))
            except ValueError:
                continue
    return values


def extract_table_protein(answer: str) -> list[float]:
    rows = [line for line in answer.split("\n") if line.startswith("|") and "prote" not in line.lower()]
    values: list[float] = []
    for row in rows:
        cells = [cell.strip() for cell in row.split("|") if cell.strip()]
        if len(cells) >= 5 and cells[0] not in {"**Total**", "Alimento"}:
            protein_cell = cells[4].lower().replace("g", "").strip()
            try:
                values.append(float(protein_cell.replace(",", ".")))
            except ValueError:
                continue
    return values


def extract_portion_g(answer: str) -> list[int]:
    return [int(match.group(1)) for match in re.finditer(r"\|\s*[^|]+\|\s*(\d+)g\s*\|", answer)]


def load_rows(*, benchmark_set: str) -> list[dict]:
    rows = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if benchmark_set == "B20":
        return rows
    return [row for row in rows if row.get("set") == benchmark_set]


def score_row(row: dict, result) -> RowScore:
    tolerance = float(row.get("kcal_tolerance_pct", DEFAULT_TOLERANCE_PCT))
    expected_mode = row["expected_mode"]
    if result.mode != expected_mode:
        return RowScore(
            row_id=row["id"],
            question=row["question"],
            status="FAIL",
            detail=f"mode expected {expected_mode}, got {result.mode}",
        )

    if expected_mode == "lookup":
        if not result.sources and row.get("expected_record_id"):
            return RowScore(row["id"], row["question"], "FAIL", "no sources")
        top = result.sources[0] if result.sources else {}
        if row.get("expected_record_id") and top.get("id") != row["expected_record_id"]:
            return RowScore(
                row["id"],
                row["question"],
                "FAIL",
                f"record expected {row['expected_record_id']}, got {top.get('id')}",
            )
        if row.get("expected_source") and top.get("source") != row["expected_source"]:
            return RowScore(
                row["id"],
                row["question"],
                "FAIL",
                f"source expected {row['expected_source']}, got {top.get('source')}",
            )
        if row.get("expected_name_contains"):
            haystack = (top.get("name") or "") + "\n" + result.answer
            if row["expected_name_contains"].lower() not in haystack.lower():
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"name missing '{row['expected_name_contains']}'",
                )
        if row.get("expected_answer_contains"):
            if row["expected_answer_contains"].lower() not in result.answer.lower():
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"answer missing '{row['expected_answer_contains']}'",
                )
        if row.get("expected_kcal") is not None:
            kcals = extract_table_kcal(result.answer)
            if not any(within_tolerance(k, row["expected_kcal"], tolerance) for k in kcals):
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"kcal expected ~{row['expected_kcal']}, got {kcals}",
                )
        if row.get("expected_kcal_total") is not None:
            kcals = extract_table_kcal(result.answer)
            total_match = re.search(
                r"\*\*Total\*\*.*?\|\s*([\d.,]+)\s*\|",
                result.answer,
            )
            total = float(total_match.group(1).replace(",", ".")) if total_match else sum(kcals)
            if not within_tolerance(total, row["expected_kcal_total"], tolerance):
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"total kcal expected ~{row['expected_kcal_total']}, got {total}",
                )
        if row.get("expected_protein") is not None:
            proteins = extract_table_protein(result.answer)
            if not any(within_tolerance(p, row["expected_protein"], tolerance) for p in proteins):
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"protein expected ~{row['expected_protein']}, got {proteins}",
                )
        if row.get("expected_portion_g") is not None:
            portions = extract_portion_g(result.answer)
            if row["expected_portion_g"] not in portions:
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"portion expected {row['expected_portion_g']}g, got {portions}",
                )
        if row.get("expected_item_count") is not None:
            item_rows = [
                line
                for line in result.answer.split("\n")
                if line.startswith("|") and "Alimento" not in line and "**Total**" not in line
            ]
            if len(item_rows) < row["expected_item_count"]:
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"expected {row['expected_item_count']} items, got {len(item_rows)}",
                )
        if row.get("expected_clarify_note"):
            lowered = result.answer.lower()
            if "default" not in lowered and "corte" not in lowered:
                return RowScore(row["id"], row["question"], "FAIL", "missing clarify note")

    if expected_mode == "compare":
        if row.get("expected_winner_contains"):
            if row["expected_winner_contains"].lower() not in result.answer.lower():
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"winner missing '{row['expected_winner_contains']}'",
                )

    if expected_mode == "substitute":
        if len(result.sources) < 2:
            return RowScore(row["id"], row["question"], "FAIL", "substitute missing second source")
        substitute = result.sources[1]
        for forbidden in row.get("forbidden_substitute_ids", []):
            if substitute.get("id") == forbidden:
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"forbidden substitute {forbidden}",
                )
        if row.get("expected_substitute_name_contains_any"):
            name_lower = substitute["name"].lower()
            if not any(token.lower() in name_lower for token in row["expected_substitute_name_contains_any"]):
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"substitute name expected one of {row['expected_substitute_name_contains_any']}",
                )
        elif row.get("expected_substitute_name_contains"):
            if row["expected_substitute_name_contains"].lower() not in substitute["name"].lower():
                return RowScore(
                    row["id"],
                    row["question"],
                    "FAIL",
                    f"substitute name missing '{row['expected_substitute_name_contains']}'",
                )

    return RowScore(row["id"], row["question"], "PASS", result.mode)


def run_benchmark(*, benchmark_set: str) -> dict:
    if not VECTORS_DB.is_file():
        raise FileNotFoundError(f"mobile vectors.db required: {VECTORS_DB}")

    assistant = MobileNutriAssistant()
    rows = load_rows(benchmark_set=benchmark_set)
    scores: list[RowScore] = []
    for row in rows:
        result = assistant.ask(row["question"], debug=True)
        scores.append(score_row(row, result))

    passed = sum(1 for score in scores if score.status == "PASS")
    return {
        "set": benchmark_set,
        "total": len(scores),
        "passed": passed,
        "pass_rate_pct": round(passed / len(scores) * 100, 1) if scores else 0.0,
        "rows": [score.__dict__ for score in scores],
    }


def print_scorecard(report: dict) -> None:
    print(f"Mobile QA benchmark — {report['set']}")
    print(f"Pass: {report['passed']}/{report['total']} ({report['pass_rate_pct']}%)")
    print()
    for row in report["rows"]:
        mark = "✅" if row["status"] == "PASS" else "❌"
        print(f"{mark} {row['row_id']}: {row['question']}")
        if row["status"] != "PASS":
            print(f"   → {row['detail']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run mobile QA benchmark (R10 / B20)")
    parser.add_argument("--set", choices=("R10", "B20"), default="B20")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument("--fail-under", type=float, default=None, help="Exit 1 if pass rate below threshold")
    parser.add_argument("--log", action="store_true", help="Write snapshot to logs/mobile-qa-b20-<date>.json")
    args = parser.parse_args()

    report = run_benchmark(benchmark_set=args.set)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_scorecard(report)

    if args.log:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / f"mobile-qa-{args.set.lower()}-{date.today().isoformat()}.json"
        log_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {log_path}")

    if args.fail_under is not None and report["pass_rate_pct"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
