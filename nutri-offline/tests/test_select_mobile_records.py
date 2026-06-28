"""Tests for mobile record tier selection (N-08-03)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import duckdb

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from _paths import FOODS_PARQUET  # noqa: E402
from select_mobile_records import (  # noqa: E402
    DEFAULT_OFF_TIER_C_SIZE,
    MobileTierSelection,
    compute_off_rank_score,
    select_mobile_records,
)


class OffRankScoreTest(unittest.TestCase):
    def test_priority_brand_scores_higher(self) -> None:
        # GIVEN two OFF rows with equal macros
        priority = {"brand": "Vigor", "energy_kcal": 100.0, "protein_g": 5.0}
        generic = {"brand": "Unknown", "energy_kcal": 100.0, "protein_g": 5.0}
        # WHEN ranked
        # THEN priority brand wins
        self.assertGreater(compute_off_rank_score(priority), compute_off_rank_score(generic))

    def test_complete_macros_score_higher_than_sparse(self) -> None:
        complete = {
            "brand": "Acme",
            "energy_kcal": 100.0,
            "protein_g": 5.0,
            "carbohydrate_g": 10.0,
            "fat_g": 2.0,
        }
        sparse = {"brand": "Acme", "energy_kcal": None, "protein_g": None}
        self.assertGreater(compute_off_rank_score(complete), compute_off_rank_score(sparse))


class SelectMobileRecordsIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not FOODS_PARQUET.is_file():
            raise unittest.SkipTest("foods.parquet required")

    def test_selects_all_taco_rows(self) -> None:
        # GIVEN real foods.parquet
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mobile_record_ids.parquet"
            summary = select_mobile_records(output_path=out, off_tier_c_size=100)
            connection = duckdb.connect(":memory:")
            taco_total = connection.execute(
                f"SELECT count(*) FROM read_parquet('{FOODS_PARQUET.as_posix()}') WHERE source = 'taco'"
            ).fetchone()[0]
            self.assertEqual(summary.tier_a_taco, taco_total)
            self.assertGreater(summary.tier_a_taco, 0)

    def test_off_tier_respects_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mobile_record_ids.parquet"
            limit = 500
            summary = select_mobile_records(output_path=out, off_tier_c_size=limit)
            self.assertLessEqual(summary.tier_c_off, limit)

    def test_vigor_product_in_default_tier_c(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mobile_record_ids.parquet"
            select_mobile_records(output_path=out, off_tier_c_size=DEFAULT_OFF_TIER_C_SIZE)
            connection = duckdb.connect(":memory:")
            vigor_in_pack = connection.execute(
                f"""
                SELECT count(*)
                FROM read_parquet('{out.as_posix()}') m
                JOIN read_parquet('{FOODS_PARQUET.as_posix()}') f ON m.id = f.id
                WHERE f.source = 'off' AND lower(f.name) LIKE '%vigor%'
                """
            ).fetchone()[0]
            self.assertGreater(vigor_in_pack, 0)

    def test_summary_reports_excluded_off_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mobile_record_ids.parquet"
            summary = select_mobile_records(output_path=out, off_tier_c_size=1000)
            self.assertGreater(summary.excluded_off, 0)
            self.assertEqual(
                summary.total_selected,
                summary.tier_a_taco + summary.tier_b_tbca + summary.tier_c_off,
            )


@unittest.skipUnless(FOODS_PARQUET.is_file(), "foods.parquet required")
class MobileTierSelectionDataclassTest(unittest.TestCase):
    def test_to_dict_contains_tiers(self) -> None:
        selection = MobileTierSelection(
            tier_a_taco=597,
            tier_b_tbca=0,
            tier_c_off=8000,
            excluded_off=24996,
            desktop_v1_scope=33593,
            total_selected=8597,
        )
        payload = selection.to_dict()
        self.assertEqual(payload["tiers"]["taco"], 597)
        self.assertEqual(payload["total_selected"], 8597)


if __name__ == "__main__":
    unittest.main()
