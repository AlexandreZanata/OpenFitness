"""Unit tests for index_catalog live snapshot fallback."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAG_DIR = Path(__file__).resolve().parents[1] / "scripts" / "rag"
sys.path.insert(0, str(RAG_DIR))

from index_catalog import index_snapshot, load_build_checkpoint  # noqa: E402


class IndexCatalogSnapshotTest(unittest.TestCase):
    def test_checkpoint_fallback_scope(self) -> None:
        checkpoint = {"scope": "all", "built": 5000, "total": 100}
        with patch("index_catalog.load_index_metadata", return_value={}), patch(
            "index_catalog.load_build_checkpoint", return_value=checkpoint
        ), patch("index_catalog.live_index_record_count", return_value=5000):
            snap = index_snapshot()
        self.assertIsNotNone(snap)
        assert snap is not None
        self.assertEqual(snap.scope, "all")
        self.assertEqual(snap.record_count, 5000)


if __name__ == "__main__":
    unittest.main()
