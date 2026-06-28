"""End-to-end NutriOffline assistant orchestrator (Phase 7)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app_paths import DEFAULT_TOP_K, MODEL_NAME
from llm_client import LlmClient
from prompt_builder import build_messages, estimate_tokens
from rag_pipeline import RagHit, RagPipeline


@dataclass
class NutriResponse:
    answer: str
    sources: list[dict[str, str]]
    rag_context: str
    rag_context_used: bool
    model: str
    latency_ms: float
    debug: dict = field(default_factory=dict)


class NutriAssistant:
    def __init__(
        self,
        *,
        rag: RagPipeline | None = None,
        llm: LlmClient | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> None:
        self.rag = rag or RagPipeline.get()
        self.llm = llm or LlmClient()
        self.top_k = top_k

    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        use_rag: bool = True,
        debug: bool = False,
    ) -> NutriResponse:
        started = time.perf_counter()
        k = top_k or self.top_k

        hits: list[RagHit] = []
        context = ""
        if use_rag:
            hits, context = self.rag.query(question, top_k=k)

        messages, used_hits = build_messages(question, hits, use_rag=use_rag)
        answer = self.llm.chat(messages)

        sources = [
            {"id": h.id, "name": h.name, "source": h.source, "score": f"{h.score:.3f}"}
            for h in used_hits
        ]

        elapsed_ms = (time.perf_counter() - started) * 1000
        debug_info: dict = {}
        if debug:
            debug_info = {
                "prompt_tokens_estimate": sum(estimate_tokens(m["content"]) for m in messages),
                "rag_hits": len(used_hits),
                "messages": messages,
            }

        return NutriResponse(
            answer=answer,
            sources=sources,
            rag_context=context,
            rag_context_used=use_rag and bool(used_hits),
            model=MODEL_NAME,
            latency_ms=round(elapsed_ms, 1),
            debug=debug_info,
        )

    def health(self) -> dict:
        return {
            "rag_index": True,
            "llm_server": self.llm.health_check(),
        }
