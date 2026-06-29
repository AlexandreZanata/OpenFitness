#!/usr/bin/env python3
"""FastAPI local server for NutriOffline (Phase 7) + RAG V2 streaming chat."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_paths import APP_HOST, APP_PORT  # noqa: E402

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import FileResponse, StreamingResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as exc:
    raise SystemExit(
        "FastAPI required — run: pip install fastapi uvicorn"
    ) from exc

from llm_client import LlmConnectionError  # noqa: E402
from runtime_router import NutriRuntimeRouter, RuntimeName  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="NutriOffline", version="1.2.0", docs_url="/docs")
router = NutriRuntimeRouter()

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    language: str = Field(default="pt-BR")
    use_rag: bool = True
    debug: bool = False
    mode: str = Field(default="auto", pattern="^(auto|lookup|llm)$")
    runtime: RuntimeName = "desktop"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    use_rag: bool = True
    debug: bool = False
    mode: str = Field(default="auto", pattern="^(auto|lookup|llm)$")
    runtime: RuntimeName = "desktop"


class NutriApiResponse(BaseModel):
    answer: str
    sources: list[dict[str, str]]
    rag_context_used: bool
    model: str
    latency_ms: float
    mode: str = "auto"
    runtime: RuntimeName = "desktop"
    cache_hit: bool = False
    rag_context: str | None = None


def _to_api_response(result, *, runtime: RuntimeName) -> NutriApiResponse:
    return NutriApiResponse(
        answer=result.answer,
        sources=result.sources,
        rag_context_used=result.rag_context_used,
        model=result.model,
        latency_ms=result.latency_ms,
        mode=result.mode,
        runtime=runtime,
        cache_hit=bool(result.debug.get("cache_hit")),
    )


def _sse_stream(body: ChatRequest):
    def generate():
        try:
            for event in router.ask_stream(
                body.message,
                runtime=body.runtime,
                top_k=body.top_k,
                use_rag=body.use_rag,
                debug=body.debug,
                history=body.history,
                mode=body.mode,
            ):
                yield f"event: {event['type']}\n"
                yield f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
        except LlmConnectionError as exc:
            payload = json.dumps({"message": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {payload}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/")
def chat_page() -> FileResponse:
    page = STATIC_DIR / "chat.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="chat.html not found")
    return FileResponse(page)


@app.get("/v1/nutri/health")
def health(runtime: RuntimeName = Query(default="desktop")) -> dict:
    status = router.health(runtime=runtime)
    if runtime == "desktop":
        status["cache"] = router.cache_stats(runtime="desktop")
    return status


@app.post("/v1/nutri/ask", response_model=NutriApiResponse)
def ask(body: AskRequest) -> NutriApiResponse:
    try:
        result = router.ask(
            body.question,
            runtime=body.runtime,
            top_k=body.top_k,
            use_rag=body.use_rag,
            debug=body.debug,
            mode=body.mode,
        )
    except LlmConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = _to_api_response(result, runtime=body.runtime)
    if body.debug:
        response.rag_context = result.rag_context
    return response


@app.post("/v1/nutri/chat", response_model=NutriApiResponse)
def chat(body: ChatRequest) -> NutriApiResponse:
    """Multi-turn chat — RAG runs on the latest user message only."""
    try:
        result = router.ask(
            body.message,
            runtime=body.runtime,
            top_k=body.top_k,
            use_rag=body.use_rag,
            debug=body.debug,
            history=body.history,
            mode=body.mode,
        )
    except LlmConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = _to_api_response(result, runtime=body.runtime)
    if body.debug:
        response.rag_context = result.rag_context
    return response


@app.post("/v1/nutri/chat/stream")
def chat_stream(body: ChatRequest) -> StreamingResponse:
    """SSE stream — lookup/mobile returns one done event; desktop LLM streams tokens."""
    return _sse_stream(body)


def main() -> int:
    uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
