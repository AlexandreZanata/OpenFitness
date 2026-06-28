"""HTTP client for local llama.cpp server (Phase 7)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

INFERENCE_DIR = Path(__file__).resolve().parents[1] / "inference"
sys.path.insert(0, str(INFERENCE_DIR))

from inference_paths import INFERENCE_URL  # noqa: E402


class LlmConnectionError(RuntimeError):
    """Raised when llama-server is not reachable."""


class LlmClient:
    """Offline-only client for OpenAI-compatible llama-server."""

    def __init__(self, base_url: str = INFERENCE_URL, *, timeout: float = 120.0) -> None:
        if "127.0.0.1" not in base_url and "localhost" not in base_url:
            raise ValueError("NutriOffline LLM client is offline-only — localhost URLs only")
        self.base_url = base_url
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        payload = json.dumps(
            {
                "model": "nutri-offline",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.base_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise LlmConnectionError(
                "llama-server not reachable — start it with: bash scripts/inference/serve.sh"
            ) from exc
        return body["choices"][0]["message"]["content"]

    def health_check(self) -> bool:
        health_url = self.base_url.replace("/v1/chat/completions", "/health")
        try:
            urllib.request.urlopen(health_url, timeout=3.0)
            return True
        except Exception:
            try:
                self.chat([{"role": "user", "content": "ping"}], max_tokens=4)
                return True
            except LlmConnectionError:
                return False
