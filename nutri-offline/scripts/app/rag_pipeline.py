"""RAG orchestration for NutriOffline app (Phase 7 + RAG V2)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
sys.path.insert(0, str(RAG_DIR))

from embed import encode_texts, load_embedder, resolve_device  # noqa: E402
from hybrid_search import AliasIndex, HybridHit, HybridSearcher  # noqa: E402
from query_rag import open_table  # noqa: E402
from rerank import (  # noqa: E402
    apply_source_boost,
    keyword_match_bonus,
    normalize_tokens,
    preparation_bonus,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from response_cache import DEFAULT_EMBED_TTL_SECONDS, TTLCache, embed_cache_key  # noqa: E402

# Backward-compatible re-exports for tests and lookup_orchestrator
_normalize_tokens = normalize_tokens


@dataclass
class RagHit:
    score: float
    id: str
    name: str
    source: str
    rag_context: str
    metadata: dict[str, Any]


def _hybrid_to_rag(hit: HybridHit) -> RagHit:
    return RagHit(
        score=hit.score,
        id=hit.id,
        name=hit.name,
        source=hit.source,
        rag_context=hit.rag_context,
        metadata=hit.metadata,
    )


class RagPipeline:
    """Embed queries and search the local LanceDB index."""

    _instance: RagPipeline | None = None

    def __init__(self, *, device: str = "cpu") -> None:
        self.device = resolve_device(device)
        self._model = load_embedder(self.device)
        self._table = open_table()
        self._embed_cache: TTLCache[list[float]] = TTLCache(max_size=512, ttl_seconds=DEFAULT_EMBED_TTL_SECONDS)
        self._hybrid = HybridSearcher(
            table=self._table,
            alias_index=AliasIndex(),
        )

    @classmethod
    def get(cls, *, device: str = "cpu") -> RagPipeline:
        if cls._instance is None:
            cls._instance = cls(device=device)
        return cls._instance

    def embed_query(self, question: str) -> list[float]:
        key = embed_cache_key(question)
        cached = self._embed_cache.get(key)
        if cached is not None:
            return cached
        vector = encode_texts(self._model, [question], show_progress=False)[0]
        self._embed_cache.set(key, vector)
        return vector

    def embed_cache_stats(self) -> dict:
        return self._embed_cache.stats()

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

    def lookup_search_query(self, food: str) -> str:
        """Resolve shorthand food token via alias table (RAG-V2-07)."""
        return self._hybrid.lookup_search_query(food)

    def search_for_lookup(
        self,
        food: str,
        *,
        top_k: int = 5,
        source_hint: str | None = None,
        prefer_branded: bool = False,
    ) -> list[RagHit]:
        """Hybrid alias + keyword + vector retrieval for deterministic lookup."""
        query = self.lookup_search_query(food)
        vector = self.embed_query(query)
        hits = self._hybrid.search(
            food,
            vector,
            top_k=top_k,
            source_hint=source_hint,
            prefer_branded=prefer_branded,
        )
        return [_hybrid_to_rag(hit) for hit in hits]

    def search_ranked(self, question: str, *, top_k: int = 5) -> list[RagHit]:
        """Vector search with keyword bonus and source boost reranking."""
        hits = self.search(question, top_k=top_k)
        with_keyword = [
            replace(hit, score=hit.score + keyword_match_bonus(question, hit.name))
            for hit in hits
        ]
        return apply_source_boost(with_keyword)  # type: ignore[return-value]

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
