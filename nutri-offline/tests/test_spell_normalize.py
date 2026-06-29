"""Unit tests for orthographic food normalization (N-09-01, BR-NORM-001)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from spell_normalize import (  # noqa: E402
    BR_NORM_001_MAX_EDIT_DISTANCE,
    SpellNormalizer,
    build_lexicon_from_sqlite,
    edit_distance,
    normalize_lookup_key,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "spell_corrections.jsonl"
LEXICON_DB = Path(__file__).resolve().parents[1] / "indexes" / "nutri-mobile" / "lexicon.db"

SEED_LEXICON = frozenset(
    {
        "arroz",
        "frango",
        "banana",
        "manga",
        "ovo",
        "pao",
        "frances",
        "carne",
        "vermelha",
        "patinho",
    }
)


class EditDistanceTest(unittest.TestCase):
    def test_identical_strings(self) -> None:
        self.assertEqual(edit_distance("arroz", "arroz"), 0)

    def test_single_substitution(self) -> None:
        self.assertEqual(edit_distance("arror", "arroz"), 1)

    def test_beyond_br_norm_limit(self) -> None:
        self.assertGreater(edit_distance("xyz", "arroz"), BR_NORM_001_MAX_EDIT_DISTANCE)


class SpellNormalizerSeedLexiconTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.normalizer = SpellNormalizer(lexicon=SEED_LEXICON)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.normalizer.close()

    def test_golden_fixture_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            result = self.normalizer.normalize_food(row["input"])
            self.assertEqual(result.text, row["expected"], row["input"])
            if row["input"] != row["expected"]:
                self.assertGreaterEqual(len(result.corrections), 1, row["input"])

    def test_no_correction_when_token_in_lexicon(self) -> None:
        result = self.normalizer.normalize_food("manga")
        self.assertEqual(result.text, "manga")
        self.assertEqual(result.corrections, ())

    def test_no_correction_when_distance_exceeds_limit(self) -> None:
        result = self.normalizer.normalize_food("zzzzz")
        self.assertEqual(result.text, "zzzzz")
        self.assertEqual(result.corrections, ())

    def test_strips_leading_preposition(self) -> None:
        result = self.normalizer.normalize_food("de arror")
        self.assertEqual(result.text, "arroz")


class SpellNormalizerPackLexiconTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not LEXICON_DB.is_file():
            raise unittest.SkipTest("lexicon.db not built — run build_mobile_lexicon.py")
        cls.normalizer = SpellNormalizer.from_lexicon_db(LEXICON_DB)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.normalizer.close()

    def test_arror_resolves_to_arroz(self) -> None:
        result = self.normalizer.normalize_food("arror")
        self.assertEqual(result.text, "arroz")

    def test_lexicon_has_minimum_coverage(self) -> None:
        self.assertGreaterEqual(len(self.normalizer.lexicon), 500)


class BuildLexiconTest(unittest.TestCase):
    def test_build_lexicon_from_sqlite(self) -> None:
        if not LEXICON_DB.is_file():
            self.skipTest("lexicon.db not built")
        lexicon, _frequencies = build_lexicon_from_sqlite(LEXICON_DB)
        self.assertIn("arroz", lexicon)
        self.assertIn("frango", lexicon)


class NormalizeLookupKeyTest(unittest.TestCase):
    def test_strips_diacritics(self) -> None:
        self.assertEqual(normalize_lookup_key("Pão"), "pao")


if __name__ == "__main__":
    unittest.main()
