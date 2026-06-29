"""Regex intent parser accuracy gate for N-09-08 / BR-INT-001."""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from intent_parser import IntentKind, ParsedIntent, parse_intent

BR_INT_001_MIN_ACCURACY = 0.90


def intent_matches_fixture(row: dict, intent: ParsedIntent) -> bool:
    expected = row["expected_kind"]
    if expected == "lookup":
        if intent.kind != IntentKind.LOOKUP or not intent.items:
            return False
        if "expected_food" in row:
            if row["expected_food"].lower() not in intent.items[0].food.lower():
                return False
        if "expected_portion_g" in row:
            if intent.items[0].portion_g != row["expected_portion_g"]:
                return False
        if row.get("highlight_field"):
            if intent.highlight_field != row["highlight_field"]:
                return False
        return True
    if expected == "compare":
        return intent.kind == IntentKind.COMPARE and intent.compare is not None
    if expected == "substitute":
        return intent.kind == IntentKind.SUBSTITUTE and intent.substitute is not None
    return intent.kind == IntentKind.REASONING


def load_intent_fixture(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evaluate_intent_regex_fixture(rows: list[dict]) -> dict:
    """Return regex intent accuracy report for BR-INT-001."""
    if not rows:
        raise ValueError("intent fixture is empty")

    matches = 0
    failures: list[dict[str, str]] = []
    for row in rows:
        intent = parse_intent(row["utterance"])
        if intent_matches_fixture(row, intent):
            matches += 1
        else:
            failures.append(
                {
                    "utterance": row["utterance"],
                    "expected_kind": row["expected_kind"],
                    "actual_kind": intent.kind.value,
                }
            )

    accuracy = matches / len(rows)
    return {
        "utterance_count": len(rows),
        "matches": matches,
        "accuracy": round(accuracy, 4),
        "threshold": BR_INT_001_MIN_ACCURACY,
        "intent_embedder_required": accuracy < BR_INT_001_MIN_ACCURACY,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Regex intent accuracy gate (BR-INT-001)")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "mobile_nl_intents.jsonl",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    rows = load_intent_fixture(args.fixture)
    report = evaluate_intent_regex_fixture(rows)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    return 1 if report["intent_embedder_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
