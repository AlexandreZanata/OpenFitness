"""Unit tests for staple substitute rules (N-10, BR-SUBST-001)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from substitute_rules import (  # noqa: E402
    is_blocked_substitute_name,
    is_staple_candidate_name,
    load_substitute_rules,
    resolve_staple_group,
    within_kcal_band,
)


class SubstituteRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = load_substitute_rules()
        cls.starch = cls.rules["staple_groups"]["starch"]

    def test_arroz_triggers_starch_group(self) -> None:
        group = resolve_staple_group(food_query="arroz", original_name="Arroz, tipo 1, cozido", rules=self.rules)
        self.assertIsNotNone(group)
        assert group is not None
        self.assertEqual(group, self.starch)

    def test_curau_is_blocked(self) -> None:
        self.assertTrue(is_blocked_substitute_name("Curau, milho verde", self.starch))

    def test_batata_doce_is_staple_candidate(self) -> None:
        self.assertTrue(is_staple_candidate_name("Batata, doce, cozida", self.starch))

    def test_kcal_band_tolerance(self) -> None:
        self.assertTrue(within_kcal_band(original_kcal=128, candidate_kcal=123, band_pct=30))
        self.assertFalse(within_kcal_band(original_kcal=128, candidate_kcal=76, band_pct=30))


if __name__ == "__main__":
    unittest.main()
