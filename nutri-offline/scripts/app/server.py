#!/usr/bin/env python3
"""FastAPI local server for NutriOffline (Phase 7 N-07-05) + browser chat UI."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_paths import APP_HOST, APP_PORT, MODEL_NAME  # noqa: E402

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as exc:
    raise SystemExit(
        "FastAPI required — run: pip install fastapi uvicorn"
    ) from exc

from llm_client import LlmConnectionError  # noqa: E402
from orchestrator import NutriAssistant  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="NutriOffline", version="1.0.0", docs_url="/docs")
assistant = NutriAssistant()

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    language: str = Field(default="pt-BR")
    use_rag: bool = True
    debug: bool = False
    mode: str = Field(default="auto", pattern="^(auto|lookup|llm)$")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    use_rag: bool = True
    debug: bool = False
    mode: str = Field(default="auto", pattern="^(auto|lookup|llm)$")


class NutriApiResponse(BaseModel):
    answer: str
    sources: list[dict[str, str]]
    rag_context_used: bool
    model: str
    latency_ms: float
    mode: str = "auto"
    rag_context: str | None = None


@app.get("/")
def chat_page() -> FileResponse:
    page = STATIC_DIR / "chat.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="chat.html not found")
    return FileResponse(page)


@app.get("/v1/nutri/health")
def health() -> dict:
    return assistant.health()


@app.post("/v1/nutri/ask", response_model=NutriApiResponse)
def ask(body: AskRequest) -> NutriApiResponse:
    try:
        result = assistant.ask(
            body.question,
            top_k=body.top_k,
            use_rag=body.use_rag,
            debug=body.debug,
            mode=body.mode,  # type: ignore[arg-type]
        )
    except LlmConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return NutriApiResponse(
        answer=result.answer,
        sources=result.sources,
        rag_context_used=result.rag_context_used,
        model=result.model,
        latency_ms=result.latency_ms,
        mode=result.mode,
        rag_context=result.rag_context if body.debug else None,
    )


@app.post("/v1/nutri/chat", response_model=NutriApiResponse)
def chat(body: ChatRequest) -> NutriApiResponse:
    """Multi-turn chat — RAG runs on the latest user message only."""
    try:
        result = assistant.ask(
            body.message,
            top_k=body.top_k,
            use_rag=body.use_rag,
            debug=body.debug,
            history=body.history,
            mode=body.mode,  # type: ignore[arg-type]
        )
    except LlmConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return NutriApiResponse(
        answer=result.answer,
        sources=result.sources,
        rag_context_used=result.rag_context_used,
        model=result.model,
        latency_ms=result.latency_ms,
        mode=result.mode,
        rag_context=result.rag_context if body.debug else None,
    )
    uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
