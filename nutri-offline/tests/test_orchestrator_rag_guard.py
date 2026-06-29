"""Unit tests for NutriOffline orchestrator RAG guard."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
sys.path.insert(0, str(APP_DIR))

from orchestrator import NutriAssistant  # noqa: E402


class OrchestratorRagGuardTest(unittest.TestCase):
    def test_llm_skipped_when_rag_enabled_but_no_hits(self) -> None:
        rag = MagicMock()
        rag.query.return_value = ([], "")
        rag.embed_cache_stats.return_value = {}
        llm = MagicMock()

        assistant = NutriAssistant(rag=rag, llm=llm, lookup=MagicMock())
        assistant.lookup.can_handle.return_value = False

        result = assistant.ask("fruta-do-sol amazônica rara", use_rag=True, mode="llm")

        llm.chat.assert_not_called()
        self.assertIn("Não encontrei", result.answer)
        self.assertFalse(result.rag_context_used)
        self.assertEqual(result.mode, "llm")


if __name__ == "__main__":
    unittest.main()
