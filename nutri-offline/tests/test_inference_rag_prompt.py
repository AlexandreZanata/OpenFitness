"""Unit tests for Phase 6 RAG prompt helpers."""

from __future__ import annotations

import unittest

import sys
from pathlib import Path

INFERENCE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "inference"
sys.path.insert(0, str(INFERENCE_DIR))

from rag_prompt import extract_kcal_from_context  # noqa: E402


class RagPromptTest(unittest.TestCase):
    def test_extract_kcal_from_context(self) -> None:
        context = (
            "[off] Arroz branco (100g): 344 kcal, P 6.4g\n"
            "[taco] Arroz, tipo 1, cozido (100g): 128 kcal, P 2.5g"
        )
        values = extract_kcal_from_context(context)
        self.assertIn(344, values)
        self.assertIn(128, values)


if __name__ == "__main__":
    unittest.main()
