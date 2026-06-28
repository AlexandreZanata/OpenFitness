"""Unit tests for RAG V2 response cache (RAG-V2-18)."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
sys.path.insert(0, str(APP_DIR))

from response_cache import TTLCache, embed_cache_key, lookup_cache_key  # noqa: E402


class ResponseCacheTest(unittest.TestCase):
    def test_lookup_key_is_stable(self) -> None:
        key_a = lookup_cache_key("arroz 100g", mode="auto", top_k=5)
        key_b = lookup_cache_key("arroz 100g", mode="auto", top_k=5)
        self.assertEqual(key_a, key_b)

    def test_ttl_cache_hit_and_miss(self) -> None:
        cache: TTLCache[str] = TTLCache(max_size=4, ttl_seconds=60)
        cache.set("k", "value")
        self.assertEqual(cache.get("k"), "value")
        self.assertEqual(cache.get("missing"), None)
        self.assertEqual(cache.stats()["hits"], 1)
        self.assertEqual(cache.stats()["misses"], 1)

    def test_ttl_cache_expires(self) -> None:
        cache: TTLCache[str] = TTLCache(max_size=4, ttl_seconds=0.01)
        cache.set("k", "value")
        time.sleep(0.02)
        self.assertIsNone(cache.get("k"))

    def test_embed_cache_key_normalizes_whitespace(self) -> None:
        self.assertEqual(embed_cache_key("  Arroz  "), embed_cache_key("arroz"))


if __name__ == "__main__":
    unittest.main()
