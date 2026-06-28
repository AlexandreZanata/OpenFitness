"""Build RAG-augmented chat messages for inference tests."""

from __future__ import annotations

import sys
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parents[1] / "rag"
sys.path.insert(0, str(RAG_DIR))

from query_rag import search  # noqa: E402

from inference_paths import SYSTEM_PROMPT_RAG


def build_rag_context_block(query: str, top_k: int = 5) -> str:
    results = search(query, top_k=top_k, device="cpu")
    lines = [item.rag_context for item in results]
    return "\n".join(lines)


def build_messages_with_rag(user_question: str, top_k: int = 5) -> list[dict[str, str]]:
    context = build_rag_context_block(user_question, top_k=top_k)
    system = f"{SYSTEM_PROMPT_RAG}\n\nContext:\n{context}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_question},
    ]


def extract_kcal_from_context(context: str) -> list[int]:
    import re

    values: list[int] = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*kcal", context, re.IGNORECASE):
        values.append(int(round(float(match.group(1)))))
    return values
