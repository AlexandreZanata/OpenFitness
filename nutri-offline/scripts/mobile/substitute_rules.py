"""Staple-food substitute filtering — BR-SUBST-001 (Phase 10)."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from mobile_paths import ROOT  # noqa: E402

SUBSTITUTE_RULES_JSON = ROOT / "config" / "semantic" / "substitute_rules.json"


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_accents).strip()


def load_substitute_rules(path: Path = SUBSTITUTE_RULES_JSON) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload


def resolve_staple_group(*, food_query: str, original_name: str, rules: dict | None = None) -> dict | None:
    """Return staple group config when the query targets a staple food (e.g. arroz)."""
    rules = rules or load_substitute_rules()
    query_key = normalize_text(food_query)
    name_key = normalize_text(original_name)
    for group in rules.get("staple_groups", {}).values():
        triggers = [normalize_text(token) for token in group.get("trigger_tokens", [])]
        if any(token in query_key or token in name_key for token in triggers):
            return group
    return None


def is_blocked_substitute_name(name: str, group: dict) -> bool:
    key = normalize_text(name)
    return any(normalize_text(token) in key for token in group.get("blocked_name_tokens", []))


def is_staple_candidate_name(name: str, group: dict) -> bool:
    key = normalize_text(name)
    if is_blocked_substitute_name(name, group):
        return False
    patterns = [normalize_text(pattern) for pattern in group.get("candidate_name_patterns", [])]
    return any(pattern in key for pattern in patterns)


def within_kcal_band(*, original_kcal: float, candidate_kcal: float, band_pct: float) -> bool:
    if original_kcal <= 0:
        return True
    delta_pct = abs(candidate_kcal - original_kcal) / original_kcal * 100
    return delta_pct <= band_pct


def staple_preference_score(name: str) -> float:
    """Higher score = better staple substitute (cooked grains/starches)."""
    key = normalize_text(name)
    score = 0.0
    if "cozid" in key or "cozida" in key or "cozido" in key:
        score += 2.0
    for marker in ("arroz", "batata", "mandioca", "cuscuz", "quinoa", "macarrao", "macarrão", "inhame"):
        if marker in key:
            score += 1.5
    if any(marker in key for marker in ("enlatado", "drenado", "conserva", "creme")):
        score -= 5.0
    return score
