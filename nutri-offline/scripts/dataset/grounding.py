"""Grounding validation for generated fine-tuning examples (Phase 4)."""

from __future__ import annotations

import re
from typing import Any

from constants import GROUNDING_TOLERANCE_PCT, SOURCE_LABELS


def within_tolerance(actual: float, expected: float, tolerance_pct: float = GROUNDING_TOLERANCE_PCT) -> bool:
    if expected == 0:
        return abs(actual - expected) <= 0.05
    return abs(actual - expected) / abs(expected) * 100 <= tolerance_pct


def extract_numbers(text: str) -> list[float]:
    return [float(match) for match in re.findall(r"\d+(?:\.\d+)?", text)]


def has_source_citation(answer: str, source_label: str) -> bool:
    if source_label.lower() in answer.lower():
        return True
    for label in SOURCE_LABELS.values():
        if label.lower() in answer.lower():
            return True
    return False


NUTRIENT_KEYS = frozenset({"energy_kcal", "protein_g", "carbohydrate_g", "fat_g", "fiber_g"})


def validate_example(example: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty = pass)."""
    errors: list[str] = []
    log_entry = example.get("generation_log") or {}
    grounding = log_entry.get("grounding") or {}
    answer = example["messages"][-1]["content"]

    if grounding.get("refusal"):
        lowered = answer.lower()
        if "não encontrei" in lowered or "did not find" in lowered:
            if not re.search(r"\d+(?:\.\d+)?\s*kcal", lowered):
                return []
        errors.append("refusal answer must acknowledge unknown without inventing kcal")
        return errors

    source_label_text = grounding.get("source_label", "")
    if not has_source_citation(answer, source_label_text):
        errors.append("missing source citation")

    values = grounding.get("values") or {}
    if isinstance(values, dict):
        for key, expected in values.items():
            if key not in NUTRIENT_KEYS or expected is None:
                continue
            formatted = (
                str(int(round(expected)))
                if key == "energy_kcal"
                else f"{expected:.1f}"
            )
            if formatted in answer or formatted.rstrip("0").rstrip(".") in answer:
                continue
            numbers = extract_numbers(answer)
            if not any(within_tolerance(n, float(expected)) for n in numbers):
                errors.append(f"value mismatch for {key}: expected ~{expected}")

    return errors


def validate_all(examples: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    passed: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    for example in examples:
        errors = validate_example(example)
        if errors:
            failed.append({**example, "validation_errors": errors})
        else:
            passed.append(example)
    return passed, failed
