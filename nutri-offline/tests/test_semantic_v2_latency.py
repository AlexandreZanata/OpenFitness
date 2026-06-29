"""Integration tests for semantic v2 latency gate (Phase 9 exit criterion)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from benchmark_semantic_v2 import LATENCY_P95_TARGET_MS, run_benchmark  # noqa: E402
from mobile_paths import VECTORS_DB  # noqa: E402


@unittest.skipUnless(VECTORS_DB.is_file(), "mobile vectors.db required")
class SemanticV2LatencyTest(unittest.TestCase):
    def test_lookup_p95_within_target(self) -> None:
        report = run_benchmark(repeats=1)
        self.assertLessEqual(report["latency_ms_p95"], LATENCY_P95_TARGET_MS)
        self.assertTrue(report["target_met"])
        self.assertGreaterEqual(report["query_count"], 8)


if __name__ == "__main__":
    unittest.main()
