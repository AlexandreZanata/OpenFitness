"""Unit tests for Phase 5 ChatML dataset loader."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "training"))
sys.path.insert(0, str(ROOT / "scripts" / "dataset"))

from constants import SYSTEM_PROMPT  # noqa: E402
from config_loader import load_training_config  # noqa: E402
from dataset_loader import (  # noqa: E402
    build_sft_dataset,
    count_system_prompt_mismatches,
    format_messages,
    load_jsonl_messages,
)


class MockTokenizer:
    """Lightweight tokenizer stub — no GPU or HuggingFace download."""

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool = False,
        add_generation_prompt: bool = False,
    ) -> str:
        parts = []
        for message in messages:
            parts.append(f"<|im_start|>{message['role']}\n{message['content']}")
        return "\n".join(parts)

    def __call__(self, text: str, *, truncation: bool = False, max_length: int | None = None):
        return {"input_ids": text.split()}


class DatasetLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ROOT / "tests" / "fixtures" / "training_sample.jsonl"
        self.tokenizer = MockTokenizer()

    def test_load_jsonl_messages_returns_two_examples(self) -> None:
        messages = load_jsonl_messages(self.fixture)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0][0]["role"], "system")

    def test_system_prompt_matches_phase4_canonical(self) -> None:
        messages = load_jsonl_messages(self.fixture)
        self.assertEqual(count_system_prompt_mismatches(messages), 0)
        self.assertEqual(messages[0][0]["content"], SYSTEM_PROMPT)

    def test_format_messages_uses_chat_template_markers(self) -> None:
        messages = load_jsonl_messages(self.fixture)
        text = format_messages(messages[0], self.tokenizer)
        self.assertIn("<|im_start|>system", text)
        self.assertIn("<|im_start|>user", text)
        self.assertIn("<|im_start|>assistant", text)

    def test_build_sft_dataset_keeps_examples_within_max_seq(self) -> None:
        dataset, stats = build_sft_dataset(
            self.fixture,
            self.tokenizer,
            max_seq_length=512,
        )
        self.assertEqual(stats["kept_examples"], 2)
        self.assertEqual(stats["dropped_over_max_seq"], 0)
        self.assertEqual(len(dataset), 2)
        self.assertIn("text", dataset.column_names)

    def test_build_sft_dataset_drops_oversized_examples(self) -> None:
        dataset, stats = build_sft_dataset(
            self.fixture,
            self.tokenizer,
            max_seq_length=3,
        )
        self.assertEqual(stats["kept_examples"], 0)
        self.assertEqual(stats["dropped_over_max_seq"], 2)
        self.assertEqual(len(dataset), 0)


class ConfigLoaderTest(unittest.TestCase):
    def test_ci_profile_overrides_epochs_and_max_steps(self) -> None:
        config_path = ROOT / "scripts" / "training" / "config.yaml"
        cfg = load_training_config(config_path, profile="ci")
        self.assertEqual(cfg["_profile"], "ci")
        self.assertEqual(cfg["max_steps"], 2)
        self.assertEqual(cfg["num_train_epochs"], 1)
        self.assertTrue(str(cfg["output_dir"]).endswith("nutri-qwen25-3b-ci-smoke"))

    def test_full_profile_uses_three_epochs(self) -> None:
        config_path = ROOT / "scripts" / "training" / "config.yaml"
        cfg = load_training_config(config_path, profile="full")
        self.assertEqual(cfg["num_train_epochs"], 3)
        self.assertNotIn("max_steps", cfg)


if __name__ == "__main__":
    unittest.main()
