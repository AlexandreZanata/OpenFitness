"""Unit tests for Layer 3 food ontology resolution (N-09-03, BR-NORM-003)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from ontology_resolver import OntologyResolver  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ontology_resolutions.jsonl"
ONTOLOGY_JSON = Path(__file__).resolve().parents[1] / "config" / "semantic" / "food_ontology.json"


class OntologyResolverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resolver = OntologyResolver.from_json(ONTOLOGY_JSON)

    def test_golden_fixture_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            result = self.resolver.resolve(row["phrase"])
            expected_node = row.get("expected_node")
            if expected_node is None:
                self.assertIsNone(result.match, row["phrase"])
                continue
            self.assertIsNotNone(result.match, row["phrase"])
            assert result.match is not None
            self.assertEqual(result.match.node_id, expected_node, row["phrase"])
            self.assertEqual(result.match.default_record_id, row["expected_record_id"], row["phrase"])
            self.assertEqual(result.needs_clarify, row["expect_clarify"], row["phrase"])

    def test_longest_phrase_match_wins(self) -> None:
        result = self.resolver.resolve("carne de vaca magra")
        self.assertIsNotNone(result.match)
        assert result.match is not None
        self.assertEqual(result.match.node_id, "meat.bovine.red")

    def test_candidate_list_includes_default(self) -> None:
        result = self.resolver.resolve("carne bovina")
        self.assertIsNotNone(result.match)
        assert result.match is not None
        self.assertIn("taco:377", result.match.candidate_record_ids)
        self.assertEqual(result.match.default_record_id, "taco:377")


if __name__ == "__main__":
    unittest.main()
