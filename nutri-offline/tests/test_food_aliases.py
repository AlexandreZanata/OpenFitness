"""Unit tests for food alias table builder (RAG-V2-07)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parents[1] / "scripts" / "rag"
sys.path.insert(0, str(RAG_DIR))

from build_food_aliases import MANUAL_ALIAS_TARGETS, _mine_aliases, build_alias_rows  # noqa: E402


class FoodAliasesTest(unittest.TestCase):
    def test_mine_aliases_from_taco_name(self) -> None:
        aliases = _mine_aliases("Arroz, tipo 1, cozido")
        self.assertIn("arroz, tipo 1, cozido", aliases)
        self.assertIn("arroz", aliases)
        self.assertIn("arroz cozido", aliases)

    def test_manual_seed_targets_exist(self) -> None:
        self.assertEqual(MANUAL_ALIAS_TARGETS["arroz"], "taco:3")
        self.assertEqual(MANUAL_ALIAS_TARGETS["banana"], "taco:182")

    def test_build_alias_rows_includes_manual_priority(self) -> None:
        records = [
            {
                "id": "taco:3",
                "source": "taco",
                "name": "Arroz, tipo 1, cozido",
                "name_normalized": "arroz, tipo 1, cozido",
            }
        ]
        rows = build_alias_rows(records)
        manual = [row for row in rows if row["alias"] == "arroz" and row["priority"] == 0]
        self.assertEqual(len(manual), 1)
        self.assertEqual(manual[0]["record_id"], "taco:3")


if __name__ == "__main__":
    unittest.main()
