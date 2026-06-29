"""Domain evaluation scoring for Phase 5 post-train validation.

Pure functions — no GPU, no model loading. Used by eval_domain.py and unit tests.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
sys.path.insert(0, str(DATASET_DIR))

from constants import SOURCE_LABELS  # noqa: E402
from grounding import extract_numbers, within_tolerance  # noqa: E402


def cites_data_source(answer: str, source_label: str = "") -> bool:
    lowered = answer.lower()
    if source_label and source_label.lower() in lowered:
        return True
    for label in SOURCE_LABELS.values():
        if label.lower() in lowered:
            return True
    return False

UNKNOWN_ACK_PATTERNS = (
    r"não\s+(tenho|sei|encontrei|disponível|posso\s+informar)",
    r"sem\s+dados",
    r"não\s+há\s+dados",
    r"dados\s+insuficientes",
    r"não\s+consta",
    r"incerto",
    r"desconhecido",
    r"não\s+está\s+na\s+(base|tabela|fonte)",
    r"informação\s+não\s+disponível",
)

PASS_THRESHOLDS = {
    "format_compliance_pct": 90.0,
    "hallucination_false_fact_pct": 10.0,
    "rag_fidelity_pct": 95.0,
}


@dataclass(frozen=True)
class ScoredRow:
    id: str
    category: str
    status: str
    detail: str
    question: str
    answer: str


def acknowledges_unknown(answer: str) -> bool:
    lowered = answer.lower()
    return any(re.search(pattern, lowered) for pattern in UNKNOWN_ACK_PATTERNS)


def has_definitive_nutrition_claim(answer: str) -> bool:
    """Heuristic: response states specific macros as facts."""
    lowered = answer.lower()
    if re.search(r"\d+(?:\.\d+)?\s*kcal", lowered):
        return True
    if re.search(r"\d+(?:\.\d+)?\s*g\b", lowered) and any(
        token in lowered for token in ("proteína", "carboidrato", "gordura", "fibra", "caloria")
    ):
        return True
    return False


def number_matches(answer: str, expected: float, tolerance_pct: float) -> bool:
    numbers = extract_numbers(answer)
    return any(within_tolerance(n, expected, tolerance_pct) for n in numbers)


def score_row(row: dict[str, Any], answer: str) -> ScoredRow:
    category = str(row.get("category", "format"))
    row_id = str(row["id"])
    question = str(row.get("question", ""))

    if category == "unknown":
        if acknowledges_unknown(answer):
            return ScoredRow(row_id, category, "PASS", "acknowledged unknown", question, answer)
        if has_definitive_nutrition_claim(answer):
            return ScoredRow(row_id, category, "FAIL", "false definitive nutrition claim", question, answer)
        return ScoredRow(row_id, category, "PASS", "no false definitive claim", question, answer)

    if category == "rag":
        expected = row.get("expects_number")
        tolerance = float(row.get("number_tolerance_pct", 2.0))
        if expected is None:
            return ScoredRow(row_id, category, "FAIL", "fixture missing expects_number", question, answer)
        if number_matches(answer, float(expected), tolerance):
            return ScoredRow(row_id, category, "PASS", f"number ~{expected} within {tolerance}%", question, answer)
        return ScoredRow(row_id, category, "FAIL", f"expected ~{expected}", question, answer)

    needs_citation = row.get(
        "expects_source_citation",
        category in {"format", "numeric", "comparison", "substitution"},
    )
    if needs_citation and not cites_data_source(answer, str(row.get("source_label", ""))):
        return ScoredRow(row_id, category, "FAIL", "missing source citation", question, answer)

    if category == "numeric":
        expected = row.get("expects_number")
        if expected is not None:
            tolerance = float(row.get("number_tolerance_pct", 5.0))
            if not number_matches(answer, float(expected), tolerance):
                return ScoredRow(
                    row_id,
                    category,
                    "FAIL",
                    f"expected number ~{expected} within {tolerance}%",
                    question,
                    answer,
                )

    if row.get("expects_answer_contains"):
        needle = str(row["expects_answer_contains"]).lower()
        if needle not in answer.lower():
            return ScoredRow(row_id, category, "FAIL", f"missing '{needle}'", question, answer)

    if category == "format" and row.get("expects_has_numbers"):
        if not extract_numbers(answer):
            return ScoredRow(row_id, category, "FAIL", "missing numeric values", question, answer)

    return ScoredRow(row_id, category, "PASS", "criteria met", question, answer)


def row_cites_source(row: dict[str, Any], answer: str) -> bool:
    category = str(row.get("category", "format"))
    if category == "unknown":
        return True
    if category == "rag":
        return True
    needs_citation = row.get(
        "expects_source_citation",
        category in {"format", "numeric", "comparison", "substitution"},
    )
    if not needs_citation:
        return True
    return cites_data_source(answer, str(row.get("source_label", "")))


def aggregate_metrics(scored: list[ScoredRow], rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not scored:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "format_compliance_pct": 0.0,
            "numeric_accuracy_pct": 0.0,
            "hallucination_false_fact_pct": 0.0,
            "rag_fidelity_pct": 0.0,
            "pass": False,
        }

    by_id = {row.id: row for row in scored}
    row_by_id = {str(r["id"]): r for r in (rows or [])}

    format_rows = [r for r in scored if r.category in {"format", "numeric", "comparison", "substitution"}]
    unknown_rows = [r for r in scored if r.category == "unknown"]
    rag_rows = [r for r in scored if r.category == "rag"]
    numeric_rows = [
        r for r in scored
        if r.category == "numeric" or (row_by_id.get(r.id, {}).get("expects_number") and r.category == "format")
    ]

    def pass_rate(rows: list[ScoredRow]) -> float:
        if not rows:
            return 100.0
        return sum(1 for r in rows if r.status == "PASS") / len(rows) * 100.0

    def fail_rate(rows: list[ScoredRow]) -> float:
        if not rows:
            return 0.0
        return sum(1 for r in rows if r.status == "FAIL") / len(rows) * 100.0

    if rows:
        citation_hits = sum(
            1 for r in format_rows if row_cites_source(row_by_id[r.id], r.answer)
        )
        format_pct = citation_hits / len(format_rows) * 100.0 if format_rows else 100.0
    else:
        format_pct = pass_rate(format_rows)

    numeric_pct = pass_rate(numeric_rows)
    hallucination_pct = fail_rate(unknown_rows)
    rag_pct = pass_rate(rag_rows)

    passed = sum(1 for r in scored if r.status == "PASS")
    gate_pass = (
        format_pct >= PASS_THRESHOLDS["format_compliance_pct"]
        and hallucination_pct <= PASS_THRESHOLDS["hallucination_false_fact_pct"]
        and (not rag_rows or rag_pct >= PASS_THRESHOLDS["rag_fidelity_pct"])
    )

    return {
        "total": len(scored),
        "passed": passed,
        "failed": len(scored) - passed,
        "format_compliance_pct": round(format_pct, 2),
        "numeric_accuracy_pct": round(numeric_pct, 2),
        "hallucination_false_fact_pct": round(hallucination_pct, 2),
        "rag_fidelity_pct": round(rag_pct, 2),
        "thresholds": PASS_THRESHOLDS,
        "pass": gate_pass,
        "source_labels_checked": list(SOURCE_LABELS.values()),
    }


def load_eval_prompts(path: Path) -> list[dict[str, Any]]:
    import json

    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
