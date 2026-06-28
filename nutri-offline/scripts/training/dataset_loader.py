"""ChatML JSONL loader for Phase 5 QLoRA SFT."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dataset"))

from constants import SYSTEM_PROMPT  # noqa: E402


class ChatTokenizer(Protocol):
    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool = False,
        add_generation_prompt: bool = False,
    ) -> str: ...

    def __call__(
        self,
        text: str,
        *,
        truncation: bool = False,
        max_length: int | None = None,
    ) -> dict[str, Any]: ...


def load_jsonl_messages(path: Path) -> list[list[dict[str, str]]]:
    """Load Phase 4 JSONL records with a messages array."""
    records: list[list[dict[str, str]]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            messages = payload.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError(f"{path}:{line_no} missing messages array")
            records.append(messages)
    return records


def count_system_prompt_mismatches(messages_list: list[list[dict[str, str]]]) -> int:
    """Return count of examples whose system prompt differs from Phase 4 canonical."""
    mismatches = 0
    for messages in messages_list:
        system = next((m for m in messages if m.get("role") == "system"), None)
        if not system or system.get("content") != SYSTEM_PROMPT:
            mismatches += 1
    return mismatches


def format_messages(messages: list[dict[str, str]], tokenizer: ChatTokenizer) -> str:
    """Apply the model chat template to a messages list."""
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)


def token_length(text: str, tokenizer: ChatTokenizer) -> int:
    encoded = tokenizer(text, truncation=False)
    return len(encoded["input_ids"])


def build_sft_dataset(
    path: Path,
    tokenizer: ChatTokenizer,
    *,
    max_seq_length: int,
) -> tuple[Any, dict[str, int | float]]:
    """Build HuggingFace Dataset with a text column; drop examples over max_seq_length."""
    from datasets import Dataset

    messages_list = load_jsonl_messages(path)
    rows: list[dict[str, str]] = []
    lengths: list[int] = []
    dropped = 0
    prompt_mismatches = count_system_prompt_mismatches(messages_list)

    for messages in messages_list:
        text = format_messages(messages, tokenizer)
        length = token_length(text, tokenizer)
        if length > max_seq_length:
            dropped += 1
            continue
        rows.append({"text": text})
        lengths.append(length)

    stats: dict[str, int | float] = {
        "source_path": str(path),
        "input_examples": len(messages_list),
        "kept_examples": len(rows),
        "dropped_over_max_seq": dropped,
        "system_prompt_mismatches": prompt_mismatches,
        "max_token_length": max(lengths) if lengths else 0,
        "mean_token_length": round(sum(lengths) / len(lengths), 1) if lengths else 0.0,
    }
    return Dataset.from_list(rows), stats
