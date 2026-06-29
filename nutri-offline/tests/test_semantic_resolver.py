"""Unit tests for semantic resolver pipeline (N-09-06)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from semantic_resolver import SemanticResolver  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "semantic_resolutions.jsonl"


class SemanticResolverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not (Path(__file__).resolve().parents[1] / "indexes" / "nutri-mobile" / "lexicon.db").is_file():
            raise unittest.SkipTest("lexicon.db not built — run build_mobile_lexicon.py")
        cls.resolver = SemanticResolver()

    def test_golden_fixture_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            result = self.resolver.resolve(row["food"])
            self.assertEqual(result.normalized, row["expected_normalized"], row["food"])
            self.assertEqual(result.primary_layer, row["expected_primary_layer"], row["food"])

    def test_debug_dict_contains_layers(self) -> None:
        result = self.resolver.resolve("de arror")
        debug = result.to_debug_dict()
        self.assertEqual(debug["normalized"], "arroz")
        self.assertEqual(debug["primary_layer"], "synonym")
        self.assertTrue(any(layer["layer"] == "spell" for layer in debug["layers"]))
        self.assertTrue(any(layer["layer"] == "synonym" for layer in debug["layers"]))


class SemanticResolverIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        lexicon = Path(__file__).resolve().parents[1] / "indexes" / "nutri-mobile" / "lexicon.db"
        vectors = Path(__file__).resolve().parents[1] / "indexes" / "nutri-mobile" / "vectors.db"
        if not lexicon.is_file() or not vectors.is_file():
            raise unittest.SkipTest("mobile pack indexes not built")
        from mobile_search import MobileSearcher  # noqa: E402

        cls.searcher = MobileSearcher()

    def test_searcher_exposes_last_resolution(self) -> None:
        self.searcher.search("de arror", top_k=3)
        resolution = self.searcher.last_resolution
        self.assertIsNotNone(resolution)
        assert resolution is not None
        self.assertEqual(resolution.normalized, "arroz")


if __name__ == "__main__":
    unittest.main()
