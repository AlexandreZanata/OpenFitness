"""RAG orchestration for NutriOffline app (Phase 7 + RAG V2)."""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
sys.path.insert(0, str(RAG_DIR))

from embed import encode_texts, load_embedder, resolve_device  # noqa: E402
from query_rag import open_table  # noqa: E402

SOURCE_BOOST: dict[str, float] = {
    "taco": 0.15,
    "tbca": 0.12,
    "fdc": 0.05,
    "off": 0.0,
}

AUTHORITY_SOURCES = ("taco", "tbca")

# Lightweight shorthand → richer search query (Phase A; full aliases in Phase B)
GENERIC_SEARCH_EXPANSIONS: dict[str, str] = {
    "arroz": "arroz tipo 1 cozido",
    "carne": "carne bovina grelhada",
    "feijão": "feijão carioca cozido",
    "feijao": "feijão carioca cozido",
    "banana": "banana prata crua",
    "ovo": "ovo de galinha cozido",
    "frango": "frango grelhado",
}


def _normalize_tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return [token for token in re.split(r"[^a-z0-9]+", stripped) if len(token) >= 2]


def keyword_match_bonus(query: str, name: str) -> float:
    """Small score bonus when query tokens appear in the candidate name."""
    query_tokens = set(_normalize_tokens(query))
    name_tokens = set(_normalize_tokens(name))
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & name_tokens)
    return min(0.12, overlap * 0.04)


def apply_source_boost(hits: list[RagHit]) -> list[RagHit]:
    """Rerank hits with source authority boost (BR-RET-001)."""
    boosted = [
        replace(hit, score=hit.score + SOURCE_BOOST.get(hit.source.lower(), 0.0))
        for hit in hits
    ]
    boosted.sort(key=lambda item: item.score, reverse=True)
    return boosted


def lookup_search_query(food: str) -> str:
    """Expand generic shorthand to a richer embedding query."""
    key = food.strip().lower()
    if key in GENERIC_SEARCH_EXPANSIONS:
        return GENERIC_SEARCH_EXPANSIONS[key]
    return food


def preparation_bonus(name: str) -> float:
    """Prefer cooked/generic table entries over raw ingredients for portions."""
    lowered = name.lower()
    bonus = 0.0
    if "cozido" in lowered or "grelhad" in lowered or "crua" in lowered:
        bonus += 0.06
    if " cru" in lowered or lowered.endswith("cru"):
        bonus -= 0.08
    return bonus


@dataclass
class RagHit:
    score: float
    id: str
    name: str
    source: str
    rag_context: str
    metadata: dict[str, Any]


class RagPipeline:
    """Embed queries and search the local LanceDB index."""

    _instance: RagPipeline | None = None

    def __init__(self, *, device: str = "cpu") -> None:
        self.device = resolve_device(device)
        self._model = load_embedder(self.device)
        self._table = open_table()

    @classmethod
    def get(cls, *, device: str = "cpu") -> RagPipeline:
        if cls._instance is None:
            cls._instance = cls(device=device)
        return cls._instance

    def embed_query(self, question: str) -> list[float]:
        return encode_texts(self._model, [question], show_progress=False)[0]

    def _rows_to_hits(self, rows: list[dict[str, Any]]) -> list[RagHit]:
        hits: list[RagHit] = []
        for row in rows:
            score = row.get("_distance")
            if score is not None:
                score = 1.0 - float(score)
            hits.append(
                RagHit(
                    score=float(score or 0.0),
                    id=row["id"],
                    name=row["name"],
                    source=row["source"],
                    rag_context=row["rag_context"],
                    metadata={
                        "energy_kcal": row.get("energy_kcal"),
                        "protein_g": row.get("protein_g"),
                        "carbohydrate_g": row.get("carbohydrate_g"),
                        "fat_g": row.get("fat_g"),
                        "serving_basis": row.get("serving_basis") or "100g",
                    },
                )
            )
        return hits

    def search(self, question: str, *, top_k: int = 5) -> list[RagHit]:
        vector = self.embed_query(question)
        rows = (
            self._table.search(vector, vector_column_name="vector")
            .limit(top_k)
            .to_list()
        )
        return self._rows_to_hits(rows)

    def search_for_lookup(
        self,
        food: str,
        *,
        top_k: int = 5,
        source_hint: str | None = None,
        prefer_branded: bool = False,
    ) -> list[RagHit]:
        """Retrieve candidates for deterministic lookup (authority + general merge)."""
        query = lookup_search_query(food)
        vector = self.embed_query(query)

        general_limit = top_k * 4 if not prefer_branded else top_k * 2
        rows = (
            self._table.search(vector, vector_column_name="vector")
            .limit(general_limit)
            .to_list()
        )

        merged: dict[str, RagHit] = {row["id"]: hit for row, hit in zip(rows, self._rows_to_hits(rows))}

        if source_hint:
            filter_sql = f"source = '{source_hint.lower()}'"
        elif not prefer_branded:
            filter_sql = "source IN ('taco', 'tbca')"
        else:
            filter_sql = None

        if filter_sql:
            authority_rows = (
                self._table.search(vector, vector_column_name="vector")
                .where(filter_sql)
                .limit(top_k * 2)
                .to_list()
            )
            for row, hit in zip(authority_rows, self._rows_to_hits(authority_rows)):
                merged.setdefault(row["id"], hit)

        hits = list(merged.values())
        scored: list[RagHit] = []
        for hit in hits:
            bonus = keyword_match_bonus(food, hit.name) + keyword_match_bonus(query, hit.name)
            bonus += preparation_bonus(hit.name)
            scored.append(replace(hit, score=hit.score + bonus))
        return apply_source_boost(scored)[: top_k * 2]

    def search_ranked(self, question: str, *, top_k: int = 5) -> list[RagHit]:
        """Vector search with keyword bonus and source boost reranking."""
        hits = self.search(question, top_k=top_k)
        with_keyword = [
            replace(hit, score=hit.score + keyword_match_bonus(question, hit.name))
            for hit in hits
        ]
        return apply_source_boost(with_keyword)

    @staticmethod
    def build_context(results: list[RagHit]) -> str:
        return "\n".join(item.rag_context for item in results)

    @staticmethod
    def build_compact_context(results: list[RagHit]) -> str:
        """Compact table context for LLM reasoning path (RAG-V2-16)."""
        lines = [
            "| Fonte | Alimento | kcal | P | C | G |",
            "|-------|----------|------|---|---|---|",
        ]
        for hit in results:
            meta = hit.metadata
            energy = meta.get("energy_kcal")
            protein = meta.get("protein_g")
            carbs = meta.get("carbohydrate_g")
            fat = meta.get("fat_g")

            def _cell(value: float | None) -> str:
                return "—" if value is None else f"{value:g}"

            lines.append(
                f"| {hit.source} | {hit.name} | {_cell(energy)} | "
                f"{_cell(protein)} | {_cell(carbs)} | {_cell(fat)} |"
            )
        return "\n".join(lines)

    def query(self, question: str, *, top_k: int = 5) -> tuple[list[RagHit], str]:
        results = self.search_ranked(question, top_k=top_k)
        return results, self.build_compact_context(results)
