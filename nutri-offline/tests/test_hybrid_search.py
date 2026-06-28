"""Unit tests for hybrid alias + keyword search (RAG-V2-06)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parents[1] / "scripts" / "rag"
APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
sys.path.insert(0, str(RAG_DIR))
sys.path.insert(0, str(APP_DIR))

from _paths import FOOD_ALIASES_PARQUET, FOODS_PARQUET  # noqa: E402
from hybrid_search import AliasIndex, KeywordSearcher  # noqa: E402


@unittest.skipUnless(FOODS_PARQUET.is_file(), "foods.parquet required")
class HybridSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.keyword = KeywordSearcher()

    def test_keyword_search_finds_taco_arroz(self) -> None:
        hits = self.keyword.search("arroz cozido", top_k=5, sources=("taco", "tbca"))
        self.assertGreaterEqual(len(hits), 1)
        self.assertTrue(any("arroz" in hit.name.lower() for hit in hits))
        self.assertEqual(hits[0].source, "taco")

    def test_alias_index_resolves_arroz_when_parquet_present(self) -> None:
        if not FOOD_ALIASES_PARQUET.is_file():
            self.skipTest("food_aliases.parquet not built yet")
        index = AliasIndex()
        matches = index.resolve("arroz")
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].record_id, "taco:3")


if __name__ == "__main__":
    unittest.main()
