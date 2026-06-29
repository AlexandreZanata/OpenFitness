"""End-to-end NutriOffline assistant orchestrator (Phase 7 + RAG V2)."""

from __future__ import annotations

import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app_paths import DEFAULT_TOP_K, LLM_MAX_TOKENS, MODEL_NAME, NO_RAG_HITS_REFUSAL
from intent_parser import IntentKind, parse_intent
from llm_client import LlmClient
from lookup_orchestrator import LookupOrchestrator, LookupResult
from prompt_builder import build_messages, estimate_tokens
from rag_pipeline import RagHit, RagPipeline
from reasoning_adapter import RagReasoningSearcher
from response_cache import DEFAULT_LOOKUP_TTL_SECONDS, TTLCache, lookup_cache_key

MOBILE_DIR = Path(__file__).resolve().parents[1] / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from reasoning_engine import CompareEngine, ReasoningResult, SubstituteEngine  # noqa: E402

ResponseMode = Literal["lookup", "llm", "auto", "compare", "substitute", "clarify"]


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
        lookup_cache: TTLCache[NutriResponse] | None = None,
    ) -> None:
        self.rag = rag or RagPipeline.get()
        self.llm = llm or LlmClient()
        self.top_k = top_k
        self.lookup = lookup or LookupOrchestrator(rag=self.rag)
        self._lookup_cache = lookup_cache or TTLCache(
            max_size=512,
            ttl_seconds=DEFAULT_LOOKUP_TTL_SECONDS,
        )
        reasoning_search = RagReasoningSearcher(rag=self.rag)
        self._compare = CompareEngine(reasoning_search, catalog="desktop")
        self._substitute = SubstituteEngine(reasoning_search, catalog="desktop")

    def cache_stats(self) -> dict[str, Any]:
        return {
            "lookup": self._lookup_cache.stats(),
            "embedding": self.rag.embed_cache_stats(),
        }

    def health(self) -> dict[str, bool]:
        rag_ok = False
        try:
            self.rag._table  # noqa: SLF001
            rag_ok = True
        except Exception:
            rag_ok = False
        return {
            "rag_index": rag_ok,
            "llm_server": self.llm.health_check(),
        }

    def _reasoning_response(
        self,
        result: ReasoningResult,
        *,
        started: float,
        debug: bool,
    ) -> NutriResponse:
        sources = [
            {"id": h.id, "name": h.name, "source": h.source, "score": f"{h.score:.3f}"}
            for h in result.hits
        ]
        debug_info: dict = {"cache_hit": False}
        if debug:
            debug_info["hits"] = len(result.hits)
        return NutriResponse(
            answer=result.answer,
            sources=sources,
            rag_context="",
            rag_context_used=bool(result.hits),
            model="rule-engine",
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
            mode=result.mode,  # type: ignore[arg-type]
            debug=debug_info,
        )

    def _lookup_response(
        self,
        result: LookupResult,
        *,
        started: float,
        debug: bool,
        cache_hit: bool = False,
    ) -> NutriResponse:
        sources = [
            {"id": h.id, "name": h.name, "source": h.source, "score": f"{h.score:.3f}"}
            for h in result.hits
        ]
        elapsed_ms = (time.perf_counter() - started) * 1000
        debug_info: dict = {"cache_hit": cache_hit}
        if debug:
            debug_info.update(
                {
                    "lookup_items": [
                        {"food": item.food, "portion_g": item.portion_g} for item in result.items
                    ],
                    "all_matched": result.all_matched,
                }
            )
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
            if not hits:
                elapsed_ms = (time.perf_counter() - started) * 1000
                return NutriResponse(
                    answer=NO_RAG_HITS_REFUSAL,
                    sources=[],
                    rag_context="",
                    rag_context_used=False,
                    model=MODEL_NAME,
                    latency_ms=round(elapsed_ms, 1),
                    mode="llm",
                    debug={"cache_hit": False, "rag_hits": 0},
                )

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
        debug_info: dict = {"cache_hit": False}
        if debug:
            debug_info.update(
                {
                    "prompt_tokens_estimate": sum(estimate_tokens(m["content"]) for m in messages),
                    "rag_hits": len(used_hits),
                    "messages": messages,
                }
            )

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

    def _response_payload(self, result: NutriResponse, *, debug: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "answer": result.answer,
            "sources": result.sources,
            "rag_context_used": result.rag_context_used,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "mode": result.mode,
            "cache_hit": result.debug.get("cache_hit", False),
        }
        if debug:
            payload["rag_context"] = result.rag_context
            payload["debug"] = result.debug
        return payload

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

        if intent.kind == IntentKind.COMPARE and intent.compare is not None:
            return self._reasoning_response(
                self._compare.execute(intent.compare),
                started=started,
                debug=debug,
            )

        if intent.kind == IntentKind.SUBSTITUTE and intent.substitute is not None:
            return self._reasoning_response(
                self._substitute.execute(intent.substitute),
                started=started,
                debug=debug,
            )

        if mode in {"auto", "lookup"} and self.lookup.can_handle(intent):
            cache_key = lookup_cache_key(question, mode=mode, top_k=k)
            cached = self._lookup_cache.get(cache_key)
            if cached is not None:
                cached.debug = {**cached.debug, "cache_hit": True}
                cached.latency_ms = round((time.perf_counter() - started) * 1000, 1)
                return cached

            lookup_result = self.lookup.execute(intent, top_k=k)
            if mode == "lookup" or intent.kind == IntentKind.LOOKUP:
                response = self._lookup_response(
                    lookup_result, started=started, debug=debug, cache_hit=False
                )
                self._lookup_cache.set(cache_key, response)
                return response

        return self._llm_response(
            question,
            started=started,
            top_k=k,
            use_rag=use_rag,
            debug=debug,
            history=history,
            max_history_turns=max_history_turns,
        )

    def ask_stream(
        self,
        question: str,
        *,
        top_k: int | None = None,
        use_rag: bool = True,
        debug: bool = False,
        history: list[dict[str, str]] | None = None,
        max_history_turns: int = 6,
        mode: ResponseMode = "auto",
    ) -> Iterator[dict[str, Any]]:
        """Yield SSE-friendly events: token, done, error."""
        started = time.perf_counter()
        k = top_k or self.top_k
        intent = parse_intent(question)

        try:
            if intent.kind == IntentKind.COMPARE and intent.compare is not None:
                result = self._reasoning_response(
                    self._compare.execute(intent.compare),
                    started=started,
                    debug=debug,
                )
                yield {"type": "done", "data": self._response_payload(result, debug=debug)}
                return

            if intent.kind == IntentKind.SUBSTITUTE and intent.substitute is not None:
                result = self._reasoning_response(
                    self._substitute.execute(intent.substitute),
                    started=started,
                    debug=debug,
                )
                yield {"type": "done", "data": self._response_payload(result, debug=debug)}
                return

            if mode in {"auto", "lookup"} and self.lookup.can_handle(intent):
                result = self.ask(
                    question,
                    top_k=k,
                    use_rag=use_rag,
                    debug=debug,
                    history=history,
                    max_history_turns=max_history_turns,
                    mode=mode,
                )
                yield {
                    "type": "done",
                    "data": self._response_payload(result, debug=debug),
                }
                return

            hits: list[RagHit] = []
            context = ""
            if use_rag:
                hits, context = self.rag.query(question, top_k=k)
                if not hits:
                    elapsed_ms = (time.perf_counter() - started) * 1000
                    payload = {
                        "answer": NO_RAG_HITS_REFUSAL,
                        "sources": [],
                        "rag_context_used": False,
                        "model": MODEL_NAME,
                        "latency_ms": round(elapsed_ms, 1),
                        "mode": "llm",
                        "cache_hit": False,
                    }
                    yield {"type": "done", "data": payload}
                    return

            messages, used_hits = build_messages(question, hits, use_rag=use_rag)
            if history:
                trimmed = [
                    m
                    for m in history[-max_history_turns * 2 :]
                    if m.get("role") in {"user", "assistant"} and m.get("content")
                ]
                messages = [messages[0], *trimmed, messages[1]]

            parts: list[str] = []
            for token in self.llm.chat_stream(
                messages,
                max_tokens=LLM_MAX_TOKENS,
                temperature=0.3,
            ):
                parts.append(token)
                yield {"type": "token", "data": {"content": token}}

            answer = "".join(parts)
            sources = [
                {"id": h.id, "name": h.name, "source": h.source, "score": f"{h.score:.3f}"}
                for h in used_hits
            ]
            elapsed_ms = (time.perf_counter() - started) * 1000
            payload = {
                "answer": answer,
                "sources": sources,
                "rag_context_used": use_rag and bool(used_hits),
                "model": MODEL_NAME,
                "latency_ms": round(elapsed_ms, 1),
                "mode": "llm",
                "cache_hit": False,
            }
            if debug:
                payload["rag_context"] = context
                payload["debug"] = {
                    "prompt_tokens_estimate": sum(estimate_tokens(m["content"]) for m in messages),
                    "rag_hits": len(used_hits),
                }
            yield {"type": "done", "data": payload}
        except Exception as exc:
            yield {"type": "error", "data": {"message": str(exc)}}
