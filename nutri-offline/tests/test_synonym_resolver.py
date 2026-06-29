"""Unit tests for Layer 2 synonym resolution (N-09-02, BR-NORM-002)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from build_synonyms import build_synonyms_db, load_manual_entries  # noqa: E402
from synonym_resolver import SynonymResolver, normalize_phrase_key  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "synonym_resolutions.jsonl"
MANUAL_SYNONYMS = Path(__file__).resolve().parents[1] / "config" / "semantic" / "manual_synonyms.json"
SYNONYMS_DB = Path(__file__).resolve().parents[1] / "indexes" / "nutri-mobile" / "synonyms.db"


class NormalizePhraseKeyTest(unittest.TestCase):
    def test_strips_accents_and_lowercases(self) -> None:
        self.assertEqual(normalize_phrase_key("Pão Francês"), "pao frances")


class ManualSynonymsFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolver = SynonymResolver.from_manual_json(MANUAL_SYNONYMS)

    def test_golden_fixture_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            result = self.resolver.resolve(row["phrase"])
            expected_id = row.get("expected_record_id")
            if expected_id is None:
                self.assertIsNone(result.primary, row["phrase"])
                continue
            self.assertIsNotNone(result.primary, row["phrase"])
            assert result.primary is not None
            self.assertEqual(result.primary.record_id, expected_id, row["phrase"])
            if "expected_label" in row:
                self.assertEqual(result.primary.label, row["expected_label"], row["phrase"])

    def test_carne_vermelha_has_multiple_candidates(self) -> None:
        result = self.resolver.resolve("carne vermelha")
        self.assertGreaterEqual(len(result.matches), 2)
        self.assertTrue(result.primary.is_default)


class BuildSynonymsDbTest(unittest.TestCase):
    def test_builds_sqlite_from_manual_entries(self) -> None:
        entries = load_manual_entries(MANUAL_SYNONYMS)
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "synonyms.db"
            summary = build_synonyms_db(entries=entries, output_path=db_path, alias_rows=[])
            self.assertGreater(summary["manual_rows"], 0)
            resolver = SynonymResolver(db_path=db_path)
            result = resolver.resolve("cacetinho")
            self.assertIsNotNone(result.primary)
            assert result.primary is not None
            self.assertEqual(result.primary.record_id, "taco:53")


class SynonymResolverPackDbTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SYNONYMS_DB.is_file():
            raise unittest.SkipTest("synonyms.db not built — run build_synonyms.py")
        cls.resolver = SynonymResolver(db_path=SYNONYMS_DB)

    def test_cacetinho_resolves_in_pack_db(self) -> None:
        result = self.resolver.resolve("cacetinho")
        self.assertIsNotNone(result.primary)
        assert result.primary is not None
        self.assertEqual(result.primary.record_id, "taco:53")


if __name__ == "__main__":
    unittest.main()
