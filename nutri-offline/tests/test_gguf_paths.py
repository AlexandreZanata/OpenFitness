"""Unit tests for GGUF path naming."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

EXPORT_DIR = Path(__file__).resolve().parents[1] / "scripts" / "export"
sys.path.insert(0, str(EXPORT_DIR))

from gguf_paths import gguf_filename, gguf_model_stem  # noqa: E402


class GgufPathsTest(unittest.TestCase):
    def test_smoke_test_adapter_stem(self) -> None:
        self.assertEqual(gguf_model_stem("smoke-test"), "nutri-qwen25-3b-smoke-test")

    def test_v1_adapter_avoids_double_prefix(self) -> None:
        self.assertEqual(gguf_model_stem("nutri-qwen25-3b-v1"), "nutri-qwen25-3b-v1")
        self.assertEqual(gguf_filename("nutri-qwen25-3b-v1"), "nutri-qwen25-3b-v1-q4_k_m.gguf")


if __name__ == "__main__":
    unittest.main()
