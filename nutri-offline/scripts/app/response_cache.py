"""In-memory LRU cache for lookup answers and query embeddings (RAG-V2-18)."""

from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")

DEFAULT_LOOKUP_TTL_SECONDS = 86_400  # 24h
DEFAULT_EMBED_TTL_SECONDS = 3_600  # 1h session-ish


@dataclass
class CacheEntry(Generic[T]):
    value: T
    expires_at: float


class TTLCache(Generic[T]):
    """Simple LRU cache with TTL expiration."""

    def __init__(self, *, max_size: int = 256, ttl_seconds: float = DEFAULT_LOOKUP_TTL_SECONDS) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [key for key, entry in self._store.items() if entry.expires_at <= now]
        for key in expired:
            del self._store[key]

    def get(self, key: str) -> T | None:
        self._purge_expired()
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        if entry.expires_at <= time.monotonic():
            del self._store[key]
            self.misses += 1
            return None
        self._store.move_to_end(key)
        self.hits += 1
        return entry.value

    def set(self, key: str, value: T) -> None:
        self._purge_expired()
        expires_at = time.monotonic() + self.ttl_seconds
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)
        self._store.move_to_end(key)
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "size": len(self._store),
            "hit_rate": round(self.hits / total, 3) if total else 0.0,
        }


def lookup_cache_key(question: str, *, mode: str, top_k: int) -> str:
    payload = json.dumps(
        {"question": question.strip().lower(), "mode": mode, "top_k": top_k},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def embed_cache_key(text: str) -> str:
    normalized = " ".join(text.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
