#!/usr/bin/env python3
"""FastAPI local server for NutriOffline (Phase 7 N-07-05)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app_paths import APP_HOST, APP_PORT, MODEL_NAME  # noqa: E402

try:
    from fastapi import FastAPI
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as exc:
    raise SystemExit(
        "FastAPI required — run: pip install fastapi uvicorn"
    ) from exc

from orchestrator import NutriAssistant  # noqa: E402

app = FastAPI(title="NutriOffline", version="1.0.0", docs_url="/docs")
assistant = NutriAssistant()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    language: str = Field(default="pt-BR")
    debug: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, str]]
    rag_context_used: bool
    model: str
    latency_ms: float
    rag_context: str | None = None


@app.get("/v1/nutri/health")
def health() -> dict:
    return assistant.health()


@app.post("/v1/nutri/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    result = assistant.ask(body.question, top_k=body.top_k, debug=body.debug)
    return AskResponse(
        answer=result.answer,
        sources=result.sources,
        rag_context_used=result.rag_context_used,
        model=result.model,
        latency_ms=result.latency_ms,
        rag_context=result.rag_context if body.debug else None,
    )


def main() -> int:
    uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
