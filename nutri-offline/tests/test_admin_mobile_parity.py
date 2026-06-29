"""Unit tests for desktop admin ↔ mobile rule-engine parity."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(MOBILE_DIR))

from intent_parser import IntentKind, parse_intent  # noqa: E402
from orchestrator import NutriAssistant  # noqa: E402
from reasoning_engine import CompareEngine, ReasoningHit, ReasoningResult, SubstituteEngine  # noqa: E402


class DesktopReasoningRoutingTest(unittest.TestCase):
    def test_compare_routes_without_llm(self) -> None:
        rag = MagicMock()
        rag.embed_cache_stats.return_value = {}
        llm = MagicMock()
        lookup = MagicMock()
        lookup.can_handle.return_value = False

        compare_result = ReasoningResult(
            answer="Frango tem mais proteína que ovo.",
            hits=[
                ReasoningHit(0.9, "taco:410", "Frango", "taco", {"protein_g": 32}),
                ReasoningHit(0.8, "taco:1", "Ovo", "taco", {"protein_g": 13}),
            ],
            mode="compare",
        )

        assistant = NutriAssistant(rag=rag, llm=llm, lookup=lookup)
        with patch.object(assistant._compare, "execute", return_value=compare_result):
            result = assistant.ask("Qual tem mais proteína: frango ou ovo?")

        llm.chat.assert_not_called()
        self.assertEqual(result.mode, "compare")
        self.assertIn("proteína", result.answer.lower())

    def test_substitute_routes_without_llm(self) -> None:
        rag = MagicMock()
        rag.embed_cache_stats.return_value = {}
        llm = MagicMock()
        lookup = MagicMock()
        lookup.can_handle.return_value = False

        substitute_result = ReasoningResult(
            answer="Batata doce é alternativa mais leve que arroz.",
            hits=[
                ReasoningHit(0.9, "taco:2", "Arroz", "taco", {"energy_kcal": 128}),
                ReasoningHit(0.8, "taco:3", "Batata", "taco", {"energy_kcal": 77}),
            ],
            mode="substitute",
        )

        assistant = NutriAssistant(rag=rag, llm=llm, lookup=lookup)
        with patch.object(assistant._substitute, "execute", return_value=substitute_result):
            result = assistant.ask("Existe opção mais leve que arroz?")

        llm.chat.assert_not_called()
        self.assertEqual(result.mode, "substitute")

    def test_intent_parser_matches_mobile_for_nl_lookup(self) -> None:
        intent = parse_intent("Quantas calorias tem 100g de arroz branco cozido?")
        self.assertEqual(intent.kind, IntentKind.LOOKUP)
        self.assertTrue(intent.items)


class RuntimeRouterParityTest(unittest.TestCase):
    def test_mobile_runtime_preserves_compare_mode(self) -> None:
        from runtime_router import NutriRuntimeRouter

        router = NutriRuntimeRouter()
        mobile = MagicMock()
        mobile.ask.return_value = MagicMock(
            answer="compare ok",
            sources=[],
            model="mobile-rules",
            latency_ms=1.0,
            mode="compare",
            debug={},
        )
        router._mobile = mobile

        result = router.ask("Qual tem mais proteína: frango ou ovo?", runtime="mobile")
        self.assertEqual(result.mode, "compare")
        mobile.ask.assert_called_once()


if __name__ == "__main__":
    unittest.main()
