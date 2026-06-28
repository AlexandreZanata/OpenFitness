"""Prompt builder with RAG context budget (Phase 7)."""

from __future__ import annotations

from app_paths import MAX_CONTEXT_TOKENS, SYSTEM_PROMPT
from rag_pipeline import RagHit


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def truncate_context(results: list[RagHit], max_tokens: int = MAX_CONTEXT_TOKENS) -> tuple[list[RagHit], str]:
    """Keep top-ranked RAG hits until token budget is reached."""
    kept: list[RagHit] = []
    lines: list[str] = []
    used = estimate_tokens(SYSTEM_PROMPT) + 64

    for hit in results:
        line = hit.rag_context
        line_tokens = estimate_tokens(line)
        if used + line_tokens > max_tokens and kept:
            break
        kept.append(hit)
        lines.append(line)
        used += line_tokens

    return kept, "\n".join(lines)


def build_messages(
    question: str,
    results: list[RagHit],
    *,
    use_rag: bool = True,
) -> tuple[list[dict[str, str]], list[RagHit]]:
    if use_rag and results:
        kept, context = truncate_context(results)
        system = f"{SYSTEM_PROMPT}\n\nContext:\n{context}"
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ], kept

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ], []
