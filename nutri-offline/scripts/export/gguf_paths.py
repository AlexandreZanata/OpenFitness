"""GGUF path helpers — avoid double prefix when adapter is already fully named."""

from __future__ import annotations

MODEL_PREFIX = "nutri-qwen25-3b-"


def gguf_model_stem(adapter_name: str) -> str:
    """Return GGUF filename stem for an adapter directory name."""
    if adapter_name.startswith(MODEL_PREFIX):
        return adapter_name
    return f"{MODEL_PREFIX}{adapter_name}"


def gguf_filename(adapter_name: str, *, quant: str = "q4_k_m") -> str:
    return f"{gguf_model_stem(adapter_name)}-{quant}.gguf"
