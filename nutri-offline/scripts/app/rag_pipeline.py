"""RAG orchestration for NutriOffline app (Phase 7)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
sys.path.insert(0, str(RAG_DIR))

from embed import encode_texts, load_embedder, resolve_device  # noqa: E402
from query_rag import RagResult, open_table  # noqa: E402


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

    def search(self, question: str, *, top_k: int = 5) -> list[RagHit]:
        vector = self.embed_query(question)
        rows = (
            self._table.search(vector, vector_column_name="vector")
            .limit(top_k)
            .to_list()
        )
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
                    },
                )
            )
        return hits

    @staticmethod
    def build_context(results: list[RagHit]) -> str:
        return "\n".join(item.rag_context for item in results)

    def query(self, question: str, *, top_k: int = 5) -> tuple[list[RagHit], str]:
        results = self.search(question, top_k=top_k)
        return results, self.build_context(results)
