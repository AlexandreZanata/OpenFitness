"""Multi-surface semantic document generation for mobile index (N-09-04).

Business rule BR-SURF-001: tier A/B records emit up to 40/30 surfaces (canonical,
alias, category, prep, FAQ); tier C OFF records emit at most 3 (name, brand, combined).
Intent prototypes are regex-first (config/semantic/intent_prototypes.json); embeddings optional.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

MOBILE_EMBED_DIM = 384

BR_SURF_001_TIER_CAPS: dict[str, int] = {
    "A": 40,
    "B": 30,
    "C": 3,
}

PREP_TERMS = frozenset(
    {
        "cozido",
        "cozida",
        "cru",
        "crua",
        "grelhado",
        "grelhada",
        "frito",
        "frita",
        "assado",
        "assada",
        "refogado",
        "refogada",
        "desidratado",
        "desidratada",
        "enlatado",
        "enlatada",
        "congelado",
        "congelada",
        "in natura",
    }
)

CATEGORY_TAGS: dict[str, tuple[str, ...]] = {
    "cereais": ("carboidrato", "cereal", "graos"),
    "carnes": ("proteina", "carne"),
    "frutas": ("fruta", "vitamina"),
    "leite": ("laticinio", "calcio"),
    "dairy": ("laticinio", "iogurte"),
}


def normalize_lookup_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def short_food_label(name: str) -> str:
    first = name.split(",")[0].strip()
    return normalize_lookup_key(first)


def _extract_prep_terms(name: str) -> tuple[str, ...]:
    lowered = normalize_lookup_key(name)
    found = [term for term in PREP_TERMS if term in lowered]
    return tuple(dict.fromkeys(found))


def _category_tags(category: str) -> tuple[str, ...]:
    key = normalize_lookup_key(category)
    tags: list[str] = []
    if category.strip():
        tags.append(category.strip())
    for prefix, extra in CATEGORY_TAGS.items():
        if prefix in key:
            tags.extend(extra)
    return tuple(dict.fromkeys(tags))


@dataclass(frozen=True)
class SemanticSurface:
    record_id: str
    surface_id: str
    surface_kind: str
    search_text: str


def _surface_id(record_id: str, kind: str, suffix: str, ordinal: int) -> str:
    safe = re.sub(r"[^a-z0-9]+", "-", normalize_lookup_key(suffix))[:32] or "default"
    return f"{record_id}:{kind}:{ordinal}:{safe}"


def _append_unique(
    surfaces: list[SemanticSurface],
    *,
    record_id: str,
    kind: str,
    text: str,
    seen: set[str],
) -> None:
    cleaned = " ".join(text.split())
    if not cleaned:
        return
    key = normalize_lookup_key(cleaned)
    if key in seen:
        return
    seen.add(key)
    ordinal = sum(1 for surface in surfaces if surface.surface_kind == kind) + 1
    surfaces.append(
        SemanticSurface(
            record_id=record_id,
            surface_id=_surface_id(record_id, kind, key, ordinal),
            surface_kind=kind,
            search_text=cleaned,
        )
    )


def generate_surfaces_for_record(
    *,
    record_id: str,
    name: str,
    name_normalized: str,
    category: str,
    source: str,
    brand: str,
    tier: str,
    aliases: list[str] | None = None,
) -> tuple[SemanticSurface, ...]:
    """Generate semantic search surfaces for one food record (BR-SURF-001)."""
    cap = BR_SURF_001_TIER_CAPS.get(tier, BR_SURF_001_TIER_CAPS["C"])
    surfaces: list[SemanticSurface] = []
    seen: set[str] = set()

    if tier == "C" or source == "off":
        _append_unique(surfaces, record_id=record_id, kind="canonical", text=name, seen=seen)
        if brand.strip():
            _append_unique(surfaces, record_id=record_id, kind="brand", text=brand, seen=seen)
            _append_unique(
                surfaces,
                record_id=record_id,
                kind="combined",
                text=f"{name} {brand}",
                seen=seen,
            )
        return tuple(surfaces[:cap])

    _append_unique(surfaces, record_id=record_id, kind="canonical", text=name, seen=seen)
    if name_normalized.strip() and normalize_lookup_key(name_normalized) != normalize_lookup_key(name):
        _append_unique(
            surfaces,
            record_id=record_id,
            kind="canonical",
            text=name_normalized,
            seen=seen,
        )

    for alias in aliases or []:
        if len(surfaces) >= cap:
            break
        _append_unique(surfaces, record_id=record_id, kind="alias", text=alias, seen=seen)

    for tag in _category_tags(category):
        if len(surfaces) >= cap:
            break
        _append_unique(surfaces, record_id=record_id, kind="category", text=tag, seen=seen)

    for prep in _extract_prep_terms(name):
        if len(surfaces) >= cap:
            break
        _append_unique(
            surfaces,
            record_id=record_id,
            kind="prep",
            text=f"{name_normalized or short_food_label(name)} {prep}",
            seen=seen,
        )

    short = short_food_label(name)
    faq_templates = (
        f"quantas calorias tem {short}",
        f"calorias de {short}",
        f"proteina em {short}",
        f"quanto de proteina tem {short}",
    )
    for faq in faq_templates:
        if len(surfaces) >= cap:
            break
        _append_unique(surfaces, record_id=record_id, kind="faq", text=faq, seen=seen)

    return tuple(surfaces[:cap])


def surface_kinds(surfaces: tuple[SemanticSurface, ...]) -> set[str]:
    return {surface.surface_kind for surface in surfaces}


def estimate_int8_vector_bytes(surface_count: int, *, dims: int = MOBILE_EMBED_DIM) -> int:
    return surface_count * dims


def load_intent_prototypes(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("intent_prototypes.json must be a JSON array")
    return payload


INTENT_PROTOTYPES_PATH = Path(__file__).resolve().parents[2] / "config" / "semantic" / "intent_prototypes.json"
INTENT_PROTOTYPES: tuple[dict[str, str], ...] = tuple(
    load_intent_prototypes(INTENT_PROTOTYPES_PATH)
    if INTENT_PROTOTYPES_PATH.is_file()
    else ()
)
