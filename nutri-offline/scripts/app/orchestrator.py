"""End-to-end NutriOffline assistant orchestrator (Phase 7 + RAG V2)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from app_paths import DEFAULT_TOP_K, LLM_MAX_TOKENS, MODEL_NAME
from intent_parser import IntentKind, parse_intent
from llm_client import LlmClient
from lookup_orchestrator import LookupOrchestrator, LookupResult
from prompt_builder import build_messages, estimate_tokens
from rag_pipeline import RagHit, RagPipeline

ResponseMode = Literal["lookup", "llm", "auto"]


@dataclass
class NutriResponse:
    answer: str
    sources: list[dict[str, str]]
    rag_context: str
    rag_context_used: bool
    model: str
    latency_ms: float
    mode: ResponseMode
    debug: dict = field(default_factory=dict)


class NutriAssistant:
    def __init__(
        self,
        *,
        rag: RagPipeline | None = None,
        llm: LlmClient | None = None,
        top_k: int = DEFAULT_TOP_K,
        lookup: LookupOrchestrator | None = None,
    ) -> None:
        self.rag = rag or RagPipeline.get()
        self.llm = llm or LlmClient()
        self.top_k = top_k
        self.lookup = lookup or LookupOrchestrator(rag=self.rag)

    def _lookup_response(
        self,
        result: LookupResult,
        *,
        started: float,
        debug: bool,
    ) -> NutriResponse:
        sources = [
            {"id": h.id, "name": h.name, "source": h.source, "score": f"{h.score:.3f}"}
            for h in result.hits
        ]
        elapsed_ms = (time.perf_counter() - started) * 1000
        debug_info: dict = {}
        if debug:
            debug_info = {
                "lookup_items": [
                    {"food": item.food, "portion_g": item.portion_g} for item in result.items
                ],
                "all_matched": result.all_matched,
            }
        return NutriResponse(
            answer=result.answer,
            sources=sources,
            rag_context="",
            rag_context_used=bool(result.hits),
            model="lookup-template",
            latency_ms=round(elapsed_ms, 1),
            mode="lookup",
            debug=debug_info,
        )

    def _llm_response(
        self,
        question: str,
        *,
        started: float,
        top_k: int,
        use_rag: bool,
        debug: bool,
        history: list[dict[str, str]] | None,
        max_history_turns: int,
    ) -> NutriResponse:
        hits: list[RagHit] = []
        context = ""
        if use_rag:
            hits, context = self.rag.query(question, top_k=top_k)

        messages, used_hits = build_messages(question, hits, use_rag=use_rag)
        if history:
            trimmed = [
                m
                for m in history[-max_history_turns * 2 :]
                if m.get("role") in {"user", "assistant"} and m.get("content")
            ]
            messages = [messages[0], *trimmed, messages[1]]
        answer = self.llm.chat(messages, max_tokens=LLM_MAX_TOKENS, temperature=0.3)

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
            mode="llm",
            debug=debug_info,
        )

    def ask(
        self,
        question: str,
        *,
        top_k: int | None = None,
        use_rag: bool = True,
        debug: bool = False,
        history: list[dict[str, str]] | None = None,
        max_history_turns: int = 6,
        mode: ResponseMode = "auto",
    ) -> NutriResponse:
        started = time.perf_counter()
        k = top_k or self.top_k
        intent = parse_intent(question)

        if mode in {"auto", "lookup"} and self.lookup.can_handle(intent):
            lookup_result = self.lookup.execute(intent, top_k=k)
            if mode == "lookup" or intent.kind == IntentKind.LOOKUP:
                return self._lookup_response(lookup_result, started=started, debug=debug)

        return self._llm_response(
            question,
            started=started,
            top_k=k,
            use_rag=use_rag,
            debug=debug,
            history=history,
            max_history_turns=max_history_turns,
        )

    def health(self) -> dict:
        return {
            "rag_index": True,
            "llm_server": self.llm.health_check(),
        }
