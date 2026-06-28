"""Embedding helpers for NutriOffline RAG (BAAI/bge-m3)."""

from __future__ import annotations

import os
from pathlib import Path

from sentence_transformers import SentenceTransformer

from _paths import EMBEDDING_MODEL, ROOT

DEFAULT_BATCH_SIZE = 64

_cached_model: SentenceTransformer | None = None
_cached_device: str | None = None


def resolve_device(requested: str = "cpu") -> str:
    import torch

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but not available")
    return requested


def load_embedder(device: str = "cpu") -> SentenceTransformer:
    global _cached_model, _cached_device

    if _cached_model is not None and _cached_device == device:
        return _cached_model

    os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
    _cached_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    _cached_device = device
    return _cached_model


def encode_texts(
    model: SentenceTransformer,
    texts: list[str],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    show_progress: bool = True,
) -> list[list[float]]:
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
    )
    return [vector.tolist() for vector in vectors]
