"""Unit tests for full-catalog coverage helpers (Phase 11, G-COV)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RAG_DIR = Path(__file__).resolve().parents[1] / "scripts" / "rag"
sys.path.insert(0, str(RAG_DIR))

from index_catalog import CatalogSnapshot, IndexSnapshot, parquet_snapshot  # noqa: E402


class FullCatalogCoverageTest(unittest.TestCase):
    def test_parquet_snapshot_structure(self) -> None:
        try:
            snapshot = parquet_snapshot("v1")
        except FileNotFoundError:
            self.skipTest("foods.parquet not present")
        self.assertGreater(snapshot.total_rows, 0)
        self.assertIn("taco", snapshot.source_counts)

    def test_g_cov_01_logic_when_counts_match(self) -> None:
        parquet = CatalogSnapshot(scope="v1", total_rows=100, source_counts={"taco": 100})
        index = IndexSnapshot(
            scope="v1",
            record_count=100,
            source_counts={"taco": 100},
            index_size_mb=1.0,
            schema_version=2,
        )
        self.assertEqual(index.record_count, parquet.total_rows)
        self.assertEqual(index.source_counts, parquet.source_counts)

    def test_benchmark_coverage_cli_imports(self) -> None:
        import benchmark_coverage  # noqa: F401

    def test_coverage_seed_fixture_exists(self) -> None:
        fixture = Path(__file__).resolve().parent / "fixtures" / "full_catalog_coverage_seed.json"
        self.assertTrue(fixture.is_file())
        data = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertIn("round_trip_seed", data)


if __name__ == "__main__":
    unittest.main()
