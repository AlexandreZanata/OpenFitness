"""Route API requests to desktop or mobile NutriOffline runtime."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Literal

from orchestrator import NutriAssistant, NutriResponse

MOBILE_DIR = Path(__file__).resolve().parents[1] / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from mobile_assistant import MobileNutriAssistant, MobileNutriResponse  # noqa: E402
from mobile_paths import EMBEDDER_ONNX, PACK_ARTIFACT, VECTORS_DB  # noqa: E402

RuntimeName = Literal["desktop", "mobile"]


def _mobile_to_nutri(result: MobileNutriResponse) -> NutriResponse:
    return NutriResponse(
        answer=result.answer,
        sources=result.sources,
        rag_context="",
        rag_context_used=bool(result.sources),
        model=result.model,
        latency_ms=result.latency_ms,
        mode=result.mode,  # type: ignore[arg-type]
        debug={**result.debug, "runtime": "mobile"},
    )


class NutriRuntimeRouter:
    """Facade over desktop (LanceDB + optional LLM) and mobile pack runtimes."""

    def __init__(self) -> None:
        self._desktop: NutriAssistant | None = None
        self._mobile: MobileNutriAssistant | None = None

    @property
    def desktop(self) -> NutriAssistant:
        if self._desktop is None:
            self._desktop = NutriAssistant()
        return self._desktop

    @property
    def mobile(self) -> MobileNutriAssistant:
        if self._mobile is None:
            self._mobile = MobileNutriAssistant()
        return self._mobile

    def health(self, *, runtime: RuntimeName = "desktop") -> dict[str, Any]:
        if runtime == "mobile":
            pack_ok = VECTORS_DB.is_file() and EMBEDDER_ONNX.is_file()
            return {
                "runtime": "mobile",
                "rag_index": pack_ok,
                "mobile_pack": PACK_ARTIFACT.is_file(),
                "vectors_db": VECTORS_DB.is_file(),
                "embedder_onnx": EMBEDDER_ONNX.is_file(),
                "llm_server": True,
                "ready": pack_ok,
            }

        desktop = self.desktop
        rag_ok = False
        try:
            desktop.rag._table  # noqa: SLF001
            rag_ok = True
        except Exception:
            rag_ok = False
        llm_ok = desktop.llm.health_check()
        return {
            "runtime": "desktop",
            "rag_index": rag_ok,
            "llm_server": llm_ok,
            "mobile_pack": PACK_ARTIFACT.is_file(),
            "ready": rag_ok,
        }

    def cache_stats(self, *, runtime: RuntimeName = "desktop") -> dict[str, Any]:
        if runtime == "mobile":
            return {"runtime": "mobile"}
        return {"runtime": "desktop", **self.desktop.cache_stats()}

    def ask(
        self,
        question: str,
        *,
        runtime: RuntimeName = "desktop",
        top_k: int = 5,
        use_rag: bool = True,
        debug: bool = False,
        history: list[dict[str, str]] | None = None,
        mode: str = "auto",
    ) -> NutriResponse:
        if runtime == "mobile":
            return _mobile_to_nutri(
                self.mobile.ask(question, top_k=top_k, debug=debug)
            )
        return self.desktop.ask(
            question,
            top_k=top_k,
            use_rag=use_rag,
            debug=debug,
            history=history,
            mode=mode,  # type: ignore[arg-type]
        )

    def ask_stream(
        self,
        question: str,
        *,
        runtime: RuntimeName = "desktop",
        top_k: int = 5,
        use_rag: bool = True,
        debug: bool = False,
        history: list[dict[str, str]] | None = None,
        mode: str = "auto",
    ):
        if runtime == "mobile":
            result = self.ask(
                question,
                runtime="mobile",
                top_k=top_k,
                debug=debug,
            )
            payload = {
                "answer": result.answer,
                "sources": result.sources,
                "rag_context_used": result.rag_context_used,
                "model": result.model,
                "latency_ms": result.latency_ms,
                "mode": result.mode,
                "cache_hit": False,
                "runtime": "mobile",
            }
            if debug:
                payload["debug"] = result.debug
            yield {"type": "done", "data": payload}
            return

        for event in self.desktop.ask_stream(
            question,
            top_k=top_k,
            use_rag=use_rag,
            debug=debug,
            history=history,
            mode=mode,  # type: ignore[arg-type]
        ):
            if event.get("type") == "done":
                event["data"]["runtime"] = "desktop"
            yield event
