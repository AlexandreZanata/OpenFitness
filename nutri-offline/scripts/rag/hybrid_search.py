"""Hybrid retrieval: alias table + keyword (DuckDB/LanceDB FTS) + vector (RAG-V2-06)."""

from __future__ import annotations

import json
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

RAG_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RAG_DIR))

from _paths import (  # noqa: E402
    FOOD_ALIASES_PARQUET,
    FOODS_PARQUET,
    INDEX_METADATA,
    SCHEMA_VERSION_V2,
)

# Reuse scoring helpers from rag layer
from rerank import apply_source_boost, keyword_match_bonus, preparation_bonus  # noqa: E402


def _normalize_lookup_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


@dataclass(frozen=True)
class AliasMatch:
    alias: str
    record_id: str
    canonical_name: str
    source: str
    priority: int


@dataclass
class HybridHit:
    score: float
    id: str
    name: str
    source: str
    rag_context: str
    metadata: dict[str, Any]
    match_kind: str = "hybrid"


class AliasIndex:
    """In-memory alias lookup loaded from food_aliases.parquet."""

    def __init__(self, path: Path = FOOD_ALIASES_PARQUET) -> None:
        self._by_alias: dict[str, list[AliasMatch]] = {}
        if path.is_file():
            self._load(path)

    @property
    def available(self) -> bool:
        return bool(self._by_alias)

    def _load(self, path: Path) -> None:
        connection = duckdb.connect(":memory:")
        rows = connection.execute(
            f"""
            SELECT alias, record_id, canonical_name, source, priority
            FROM read_parquet('{path.as_posix()}')
            ORDER BY alias, priority, record_id
            """
        ).fetchall()
        for alias, record_id, canonical_name, source, priority in rows:
            match = AliasMatch(
                alias=str(alias),
                record_id=str(record_id),
                canonical_name=str(canonical_name),
                source=str(source),
                priority=int(priority),
            )
            self._by_alias.setdefault(match.alias, []).append(match)

    def resolve(self, food: str) -> list[AliasMatch]:
        key = _normalize_lookup_key(food)
        if key in self._by_alias:
            return list(self._by_alias[key])
        # Prefix: "arroz branco" may match alias "arroz" only when food is single token
        return []


class KeywordSearcher:
    """DuckDB keyword search sidecar on foods.parquet (works with v1 or v2 index)."""

    def __init__(self, parquet: Path = FOODS_PARQUET) -> None:
        self.parquet = parquet
        self._connection = duckdb.connect(":memory:")

    def search(
        self,
        food: str,
        *,
        top_k: int = 10,
        source_filter: str | None = None,
        sources: tuple[str, ...] | None = None,
    ) -> list[HybridHit]:
        if not self.parquet.is_file():
            return []

        tokens = [_normalize_lookup_key(part) for part in food.split() if len(part) >= 2]
        if not tokens:
            return []

        conditions = " AND ".join(
            f"name_normalized LIKE '%' || ? || '%'" for _ in tokens
        )
        params: list[Any] = list(tokens)

        source_clause = ""
        if source_filter:
            source_clause = " AND source = ?"
            params.append(source_filter)
        elif sources:
            placeholders = ", ".join("?" for _ in sources)
            source_clause = f" AND source IN ({placeholders})"
            params.extend(sources)

        query = f"""
            SELECT
                id, source, name, serving_basis,
                energy_kcal, protein_g, carbohydrate_g, fat_g
            FROM read_parquet('{self.parquet.as_posix()}')
            WHERE {conditions}{source_clause}
            ORDER BY
                CASE WHEN energy_kcal IS NULL THEN 1 ELSE 0 END,
                CASE source WHEN 'taco' THEN 0 WHEN 'tbca' THEN 1 WHEN 'fdc' THEN 2 ELSE 3 END,
                length(name)
            LIMIT ?
        """
        params.append(top_k)
        rows = self._connection.execute(query, params).fetchall()
        hits: list[HybridHit] = []
        for idx, row in enumerate(rows):
            overlap = keyword_match_bonus(food, row[2])
            score = 0.55 + overlap + (0.03 * max(0, top_k - idx))
            hits.append(
                HybridHit(
                    score=score,
                    id=row[0],
                    name=row[2],
                    source=row[1],
                    rag_context="",
                    metadata={
                        "energy_kcal": row[4],
                        "protein_g": row[5],
                        "carbohydrate_g": row[6],
                        "fat_g": row[7],
                        "serving_basis": row[3] or "100g",
                    },
                    match_kind="keyword",
                )
            )
        return hits


def index_supports_hybrid_fts() -> bool:
    if not INDEX_METADATA.is_file():
        return False
    metadata = json.loads(INDEX_METADATA.read_text(encoding="utf-8"))
    return metadata.get("schema_version", 1) >= SCHEMA_VERSION_V2 and metadata.get("fts_index", False)


def _row_to_hit(row: dict[str, Any], *, score: float, match_kind: str) -> HybridHit:
    distance = row.get("_distance")
    if distance is not None and match_kind != "alias":
        score = max(score, 1.0 - float(distance))
    relevance = row.get("_relevance_score")
    if relevance is not None:
        score = float(relevance)

    return HybridHit(
        score=score,
        id=str(row["id"]),
        name=str(row["name"]),
        source=str(row["source"]),
        rag_context=str(row.get("rag_context") or ""),
        metadata={
            "energy_kcal": row.get("energy_kcal"),
            "protein_g": row.get("protein_g"),
            "carbohydrate_g": row.get("carbohydrate_g"),
            "fat_g": row.get("fat_g"),
            "serving_basis": row.get("serving_basis") or "100g",
            "name_normalized": row.get("name_normalized"),
            "is_generic": row.get("is_generic"),
            "source_tier": row.get("source_tier"),
        },
        match_kind=match_kind,
    )


def _fetch_records_by_ids(table: Any, record_ids: list[str]) -> list[HybridHit]:
    if not record_ids:
        return []
    id_list = ", ".join(f"'{record_id}'" for record_id in record_ids)
    rows = table.search().where(f"id IN ({id_list})").limit(len(record_ids)).to_list()
    by_id = {row["id"]: row for row in rows}
    hits: list[HybridHit] = []
    for record_id in record_ids:
        row = by_id.get(record_id)
        if row is None:
            continue
        hits.append(_row_to_hit(row, score=0.98, match_kind="alias"))
    return hits


def _merge_hits(*groups: list[HybridHit]) -> list[HybridHit]:
    merged: dict[str, HybridHit] = {}
    for group in groups:
        for hit in group:
            existing = merged.get(hit.id)
            if existing is None or hit.score > existing.score:
                merged[hit.id] = hit
            else:
                merged[hit.id] = HybridHit(
                    score=max(existing.score, hit.score),
                    id=existing.id,
                    name=existing.name,
                    source=existing.source,
                    rag_context=existing.rag_context or hit.rag_context,
                    metadata=existing.metadata or hit.metadata,
                    match_kind=existing.match_kind if existing.score >= hit.score else hit.match_kind,
                )
    return list(merged.values())


def _macro_completeness_bonus(metadata: dict[str, Any]) -> float:
    if metadata.get("energy_kcal") is not None:
        return 0.08
    return -0.15


def _finalize_scores(hits: list[HybridHit], *, food: str, query: str) -> list[HybridHit]:
    scored: list[HybridHit] = []
    for hit in hits:
        bonus = keyword_match_bonus(food, hit.name) + keyword_match_bonus(query, hit.name)
        bonus += preparation_bonus(hit.name)
        bonus += _macro_completeness_bonus(hit.metadata)
        scored.append(
            HybridHit(
                score=hit.score + bonus,
                id=hit.id,
                name=hit.name,
                source=hit.source,
                rag_context=hit.rag_context,
                metadata=hit.metadata,
                match_kind=hit.match_kind,
            )
        )
    boosted = apply_source_boost(scored)  # type: ignore[arg-type]
    return boosted  # type: ignore[return-value]


class HybridSearcher:
    """Fuse alias, keyword, vector, and optional LanceDB FTS results."""

    def __init__(
        self,
        *,
        table: Any,
        alias_index: AliasIndex | None = None,
        keyword_searcher: KeywordSearcher | None = None,
    ) -> None:
        self.table = table
        self.alias_index = alias_index or AliasIndex()
        self.keyword_searcher = keyword_searcher or KeywordSearcher()
        self._use_lance_fts = index_supports_hybrid_fts()

    def lookup_search_query(self, food: str) -> str:
        matches = self.alias_index.resolve(food)
        if matches:
            return matches[0].canonical_name
        return food

    def search(
        self,
        food: str,
        vector: list[float],
        *,
        top_k: int = 5,
        source_hint: str | None = None,
        prefer_branded: bool = False,
    ) -> list[HybridHit]:
        query = self.lookup_search_query(food)
        groups: list[list[HybridHit]] = []

        alias_matches = self.alias_index.resolve(food)
        if alias_matches and not prefer_branded:
            groups.append(_fetch_records_by_ids(self.table, [m.record_id for m in alias_matches[:3]]))

        if self._use_lance_fts:
            try:
                from lancedb.rerankers import RRFReranker

                builder = (
                    self.table.search(
                        query,
                        query_type="hybrid",
                        vector_column_name="vector",
                        fts_columns="search_text",
                    )
                    .vector(vector)
                    .rerank(RRFReranker())
                    .limit(top_k * 3)
                )
                if source_hint:
                    builder = builder.where(f"source = '{source_hint.lower()}'")
                elif not prefer_branded:
                    builder = builder.where("source IN ('taco', 'tbca')")
                rows = builder.to_list()
                groups.append([_row_to_hit(row, score=0.0, match_kind="hybrid") for row in rows])
            except Exception:
                self._use_lance_fts = False

        if not self._use_lance_fts:
            vector_rows = (
                self.table.search(vector, vector_column_name="vector")
                .limit(top_k * 4 if not prefer_branded else top_k * 2)
                .to_list()
            )
            groups.append(
                [_row_to_hit(row, score=0.0, match_kind="vector") for row in vector_rows]
            )

            if source_hint:
                source_filter: str | None = source_hint.lower()
                source_tuple: tuple[str, ...] | None = None
            elif prefer_branded:
                source_filter = None
                source_tuple = None
            else:
                source_filter = None
                source_tuple = ("taco", "tbca")

            groups.append(
                self.keyword_searcher.search(
                    query,
                    top_k=top_k * 2,
                    source_filter=source_filter,
                    sources=source_tuple,
                )
            )

            if source_hint or not prefer_branded:
                filter_sql = (
                    f"source = '{source_hint.lower()}'"
                    if source_hint
                    else ("source IN ('taco', 'tbca')" if not prefer_branded else None)
                )
                if filter_sql:
                    authority_rows = (
                        self.table.search(vector, vector_column_name="vector")
                        .where(filter_sql)
                        .limit(top_k * 2)
                        .to_list()
                    )
                    groups.append(
                        [
                            _row_to_hit(row, score=0.0, match_kind="vector")
                            for row in authority_rows
                        ]
                    )

        merged = _merge_hits(*groups)
        ranked = _finalize_scores(merged, food=food, query=query)
        return ranked[: top_k * 2]
