"""Hybrid retrieval over mobile sqlite index (N-08-08)."""

from __future__ import annotations

import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
sys.path.insert(0, str(RAG_DIR))

from rerank import apply_source_boost, keyword_match_bonus, preparation_bonus  # noqa: E402

from mobile_paths import FOOD_ONTOLOGY_JSON, LEXICON_DB, SYNONYMS_DB, VECTORS_DB  # noqa: E402
from mobile_embedder import MobileEmbedder  # noqa: E402
from mobile_sqlite import connect  # noqa: E402
from ontology_resolver import OntologyResolver  # noqa: E402
from semantic_resolver import SemanticResolver  # noqa: E402
from spell_normalize import SpellNormalizer  # noqa: E402
from synonym_resolver import SynonymResolver  # noqa: E402


def _normalize_lookup_key(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


@dataclass
class MobileHit:
    score: float
    id: str
    name: str
    source: str
    metadata: dict[str, Any]
    match_kind: str = "hybrid"


class MobileSearcher:
    def __init__(
        self,
        *,
        vectors_db: Path = VECTORS_DB,
        lexicon_db: Path = LEXICON_DB,
        embedder: MobileEmbedder | None = None,
        spell_normalizer: SpellNormalizer | None = None,
        synonym_resolver: SynonymResolver | None = None,
        ontology_resolver: OntologyResolver | None = None,
        semantic_resolver: SemanticResolver | None = None,
    ) -> None:
        if not vectors_db.is_file():
            raise FileNotFoundError(f"vectors.db not found: {vectors_db}")
        self._vectors_db = vectors_db
        self._lexicon_db = lexicon_db if lexicon_db.is_file() else None
        self._embedder = embedder or MobileEmbedder()
        self._spell_normalizer = spell_normalizer
        if self._spell_normalizer is None and self._lexicon_db is not None:
            self._spell_normalizer = SpellNormalizer.from_lexicon_db(self._lexicon_db)
        self._synonym_resolver = synonym_resolver
        if self._synonym_resolver is None and SYNONYMS_DB.is_file():
            self._synonym_resolver = SynonymResolver.from_db(SYNONYMS_DB)
        self._ontology_resolver = ontology_resolver
        if self._ontology_resolver is None and FOOD_ONTOLOGY_JSON.is_file():
            self._ontology_resolver = OntologyResolver.from_json(FOOD_ONTOLOGY_JSON)
        self._semantic = semantic_resolver or SemanticResolver(
            spell_normalizer=self._spell_normalizer,
            synonym_resolver=self._synonym_resolver,
            ontology_resolver=self._ontology_resolver,
        )
        self._last_resolution = None

    @property
    def last_resolution(self):
        return self._last_resolution

    def normalize_food_query(self, food: str) -> tuple[str, tuple[dict[str, str], ...]]:
        resolution = self._semantic.resolve(food)
        self._last_resolution = resolution
        spell_debug = tuple(
            layer for layer in resolution.layers if layer.get("layer") == "spell"
        )
        return resolution.normalized, spell_debug

    def _synonym_hits(self, food: str) -> list[MobileHit]:
        if self._synonym_resolver is None:
            return []
        result = self._synonym_resolver.resolve(food)
        if not result.matches:
            return []
        record_ids = [match.record_id for match in result.matches]
        hits = self._fetch_by_ids(record_ids)
        default_id = result.primary.record_id if result.primary else None
        enriched: list[MobileHit] = []
        for hit in hits:
            score = 1.05 if hit.id == default_id else 1.02
            metadata = dict(hit.metadata)
            if hit.id == default_id and result.primary and result.primary.label:
                metadata["synonym_label"] = result.primary.label
            enriched.append(
                MobileHit(
                    score=score,
                    id=hit.id,
                    name=hit.name,
                    source=hit.source,
                    metadata=metadata,
                    match_kind="synonym",
                )
            )
        enriched.sort(key=lambda item: item.score, reverse=True)
        return enriched

    def _ontology_hits(self, food: str) -> list[MobileHit]:
        if self._ontology_resolver is None:
            return []
        result = self._ontology_resolver.resolve(food)
        if result.match is None:
            return []
        record_ids = list(result.match.candidate_record_ids)
        hits = self._fetch_by_ids(record_ids)
        default_id = result.match.default_record_id
        enriched: list[MobileHit] = []
        for hit in hits:
            score = 1.04 if hit.id == default_id else 1.01
            metadata = dict(hit.metadata)
            if hit.id == default_id:
                if result.match.default_label:
                    metadata["ontology_label"] = result.match.default_label
                if result.clarify_note:
                    metadata["ontology_clarify_note"] = result.clarify_note
                metadata["ontology_node_id"] = result.match.node_id
            enriched.append(
                MobileHit(
                    score=score,
                    id=hit.id,
                    name=hit.name,
                    source=hit.source,
                    metadata=metadata,
                    match_kind="ontology",
                )
            )
        enriched.sort(key=lambda item: item.score, reverse=True)
        return enriched

    def food_for_overlap(self, food: str) -> str:
        """Return a canonical food label for token-overlap checks after normalization."""
        resolution = self._semantic.resolve(food)
        self._last_resolution = resolution
        normalized = resolution.normalized
        synonym_hits = self._synonym_hits(normalized)
        if synonym_hits:
            return synonym_hits[0].name
        ontology_hits = self._ontology_hits(normalized)
        if ontology_hits:
            return ontology_hits[0].name
        alias_hits = self._alias_hits(normalized)
        if alias_hits:
            return alias_hits[0].name
        return normalized

    def lookup_search_query(self, food: str) -> str:
        if self._lexicon_db is None:
            return food
        key = _normalize_lookup_key(food)
        connection = connect(str(self._lexicon_db), readonly=True)
        row = connection.execute(
            """
            SELECT canonical_name FROM aliases
            WHERE alias = ?
            ORDER BY priority, record_id
            LIMIT 1
            """,
            (key,),
        ).fetchone()
        connection.close()
        return row[0] if row else food

    def _fetch_by_ids(self, record_ids: list[str]) -> list[MobileHit]:
        if not record_ids:
            return []
        placeholders = ", ".join("?" for _ in record_ids)
        connection = connect(str(self._vectors_db), readonly=True)
        rows = connection.execute(
            f"""
            SELECT id, source, name, energy_kcal, protein_g, carbohydrate_g, fat_g,
                   fiber_g, serving_basis, category, brand
            FROM food_meta
            WHERE id IN ({placeholders})
            """,
            record_ids,
        ).fetchall()
        connection.close()
        by_id = {row[0]: row for row in rows}
        hits: list[MobileHit] = []
        for record_id in record_ids:
            row = by_id.get(record_id)
            if row is None:
                continue
            hits.append(self._row_to_hit(row, score=0.98, match_kind="alias"))
        return hits

    @staticmethod
    def _row_to_hit(row: tuple, *, score: float, match_kind: str) -> MobileHit:
        return MobileHit(
            score=score,
            id=str(row[0]),
            name=str(row[2]),
            source=str(row[1]),
            metadata={
                "energy_kcal": row[3],
                "protein_g": row[4],
                "carbohydrate_g": row[5],
                "fat_g": row[6],
                "fiber_g": row[7],
                "serving_basis": row[8] or "100g",
                "category": row[9],
                "brand": row[10],
            },
            match_kind=match_kind,
        )

    def _alias_hits(self, food: str) -> list[MobileHit]:
        if self._lexicon_db is None:
            return []
        key = _normalize_lookup_key(food)
        connection = connect(str(self._lexicon_db), readonly=True)
        rows = connection.execute(
            """
            SELECT record_id FROM aliases
            WHERE alias = ?
            ORDER BY priority, record_id
            LIMIT 3
            """,
            (key,),
        ).fetchall()
        connection.close()
        return self._fetch_by_ids([row[0] for row in rows])

    def _keyword_hits(self, query: str, *, top_k: int, sources: tuple[str, ...] | None) -> list[MobileHit]:
        if self._lexicon_db is None:
            return self._metadata_keyword_hits(query, top_k=top_k, sources=sources)

        tokens = [_normalize_lookup_key(part) for part in query.split() if len(part) >= 2]
        if not tokens:
            return []
        match_expr = " AND ".join(f'search_text : "{token}"' for token in tokens)
        source_clause = ""
        params: list[Any] = []
        if sources:
            source_clause = f" AND source IN ({', '.join('?' for _ in sources)})"
            params.extend(sources)

        connection = connect(str(self._lexicon_db), readonly=True)
        rows = connection.execute(
            f"""
            SELECT record_id, source, name
            FROM food_fts
            WHERE food_fts MATCH ?
            {source_clause}
            LIMIT ?
            """,
            (match_expr, *params, top_k),
        ).fetchall()
        connection.close()
        return self._fetch_by_ids([row[0] for row in rows])

    def _metadata_keyword_hits(
        self,
        query: str,
        *,
        top_k: int,
        sources: tuple[str, ...] | None,
    ) -> list[MobileHit]:
        tokens = [_normalize_lookup_key(part) for part in query.split() if len(part) >= 2]
        if not tokens:
            return []
        conditions = " AND ".join("name_normalized LIKE '%' || ? || '%'" for _ in tokens)
        params: list[Any] = list(tokens)
        source_clause = ""
        if sources:
            source_clause = f" AND source IN ({', '.join('?' for _ in sources)})"
            params.extend(sources)
        params.append(top_k)
        connection = connect(str(self._vectors_db), readonly=True)
        rows = connection.execute(
            f"""
            SELECT id, source, name, energy_kcal, protein_g, carbohydrate_g, fat_g,
                   fiber_g, serving_basis, category, brand
            FROM food_meta
            WHERE {conditions}{source_clause}
            ORDER BY CASE source WHEN 'taco' THEN 0 WHEN 'tbca' THEN 1 ELSE 2 END, length(name)
            LIMIT ?
            """,
            params,
        ).fetchall()
        connection.close()
        hits: list[MobileHit] = []
        for idx, row in enumerate(rows):
            overlap = keyword_match_bonus(query, row[2])
            hits.append(
                self._row_to_hit(row, score=0.55 + overlap + 0.03 * max(0, top_k - idx), match_kind="keyword")
            )
        return hits

    def _vector_hits(
        self,
        vector: list[float],
        *,
        top_k: int,
        source_filter: str | None,
        sources: tuple[str, ...] | None,
    ) -> list[MobileHit]:
        connection = connect(str(self._vectors_db), readonly=True)
        vec_rows = connection.execute(
            """
            SELECT rowid, distance FROM food_vec
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
            """,
            (np.asarray(vector, dtype=np.float32), top_k * 4),
        ).fetchall()
        if not vec_rows:
            connection.close()
            return []

        rowids = [row[0] for row in vec_rows]
        placeholders = ", ".join("?" for _ in rowids)
        meta_rows = connection.execute(
            f"""
            SELECT rowid, id, source, name, energy_kcal, protein_g, carbohydrate_g, fat_g,
                   fiber_g, serving_basis, category, brand
            FROM food_meta
            WHERE rowid IN ({placeholders})
            """,
            rowids,
        ).fetchall()
        connection.close()
        distance_by_rowid = {row[0]: row[1] for row in vec_rows}
        hits: list[MobileHit] = []
        for row in meta_rows:
            source = str(row[2])
            if source_filter and source != source_filter:
                continue
            if sources and source not in sources:
                continue
            distance = distance_by_rowid.get(row[0], 1.0)
            score = max(0.0, 1.0 - float(distance))
            hits.append(self._row_to_hit(row[1:], score=score, match_kind="vector"))
        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]

    def search(
        self,
        food: str,
        *,
        top_k: int = 5,
        source_hint: str | None = None,
        prefer_branded: bool = False,
    ) -> list[MobileHit]:
        food, _spell_debug = self.normalize_food_query(food)
        query = self.lookup_search_query(food)
        vector = self._embedder.encode([query])[0]
        groups: list[list[MobileHit]] = []

        if not prefer_branded:
            synonym_hits = self._synonym_hits(food)
            groups.append(synonym_hits)
            if not synonym_hits:
                groups.append(self._ontology_hits(food))
            groups.append(self._alias_hits(food))

        if source_hint:
            source_filter = source_hint.lower()
            source_tuple = None
        elif prefer_branded:
            source_filter = None
            source_tuple = None
        else:
            source_filter = None
            source_tuple = ("taco", "tbca")

        groups.append(
            self._vector_hits(
                vector,
                top_k=top_k,
                source_filter=source_filter,
                sources=source_tuple,
            )
        )
        groups.append(
            self._keyword_hits(query, top_k=top_k * 2, sources=source_tuple)
        )

        merged: dict[str, MobileHit] = {}
        for group in groups:
            for hit in group:
                existing = merged.get(hit.id)
                if existing is None or hit.score > existing.score:
                    merged[hit.id] = hit

        if prefer_branded:
            food_tokens = [_normalize_lookup_key(part) for part in food.split() if len(part) >= 3]
            if food_tokens:
                branded_hits = {
                    hit_id: hit
                    for hit_id, hit in merged.items()
                    if all(
                        token in _normalize_lookup_key(hit.name)
                        or token in _normalize_lookup_key(str(hit.metadata.get("brand") or ""))
                        for token in food_tokens
                    )
                }
                if branded_hits:
                    merged = branded_hits

        scored: list[MobileHit] = []
        for hit in merged.values():
            bonus = keyword_match_bonus(food, hit.name) + keyword_match_bonus(query, hit.name)
            bonus += preparation_bonus(hit.name)
            if hit.metadata.get("energy_kcal") is not None:
                bonus += 0.08
            else:
                bonus -= 0.15
            scored.append(
                MobileHit(
                    score=hit.score + bonus,
                    id=hit.id,
                    name=hit.name,
                    source=hit.source,
                    metadata=hit.metadata,
                    match_kind=hit.match_kind,
                )
            )
        boosted = apply_source_boost(scored)  # type: ignore[arg-type]
        return boosted[: top_k * 2]

    def search_category(
        self,
        category: str,
        *,
        exclude_id: str | None = None,
        top_k: int = 20,
    ) -> list[MobileHit]:
        connection = connect(str(self._vectors_db), readonly=True)
        rows = connection.execute(
            """
            SELECT id, source, name, energy_kcal, protein_g, carbohydrate_g, fat_g,
                   fiber_g, serving_basis, category, brand
            FROM food_meta
            WHERE category != '' AND lower(category) LIKE '%' || lower(?) || '%'
            ORDER BY CASE source WHEN 'taco' THEN 0 WHEN 'tbca' THEN 1 ELSE 2 END
            LIMIT ?
            """,
            (category, top_k * 3),
        ).fetchall()
        connection.close()
        hits = [self._row_to_hit(row, score=0.5, match_kind="category") for row in rows]
        if exclude_id:
            hits = [hit for hit in hits if hit.id != exclude_id]
        return hits[:top_k]
