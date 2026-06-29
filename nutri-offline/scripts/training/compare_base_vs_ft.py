#!/usr/bin/env python3
"""Phase 5 base vs fine-tuned qualitative comparison report."""

from __future__ import annotations

import argparse
import gc
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TRAINING_DIR = Path(__file__).resolve().parent
DATASET_DIR = TRAINING_DIR.parent / "dataset"
sys.path.insert(0, str(TRAINING_DIR))

from _paths import COMPARISON_PROMPTS, DEFAULT_ADAPTER, DEFAULT_CONFIG, LOG_DIR, ROOT
from config_loader import load_training_config
from eval_domain import build_messages, generate_answer, load_eval_prompts

sys.path.insert(0, str(DATASET_DIR))
from constants import SYSTEM_PROMPT
from eval_scoring import score_row

os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
os.environ.setdefault("UNSLOTH_USE_FP16", "1")


def load_inference_model(model_name: str, max_seq_length: int):
    import unsloth  # noqa: F401
    import torch
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=torch.float16,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def run_side(model, tokenizer, rows: list[dict[str, Any]], *, max_new_tokens: int) -> dict[str, str]:
    answers: dict[str, str] = {}
    for row in rows:
        messages = build_messages(row)
        answers[str(row["id"])] = generate_answer(model, tokenizer, messages, max_new_tokens=max_new_tokens)
    return answers


def write_report(
    path: Path,
    rows: list[dict[str, Any]],
    base_answers: dict[str, str],
    ft_answers: dict[str, str],
) -> None:
    lines = [
        "# Base vs fine-tuned comparison (Phase 5)",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "| ID | Category | Base score | FT score | Question |",
        "|----|----------|------------|----------|----------|",
    ]
    for row in rows:
        row_id = str(row["id"])
        base_score = score_row(row, base_answers[row_id])
        ft_score = score_row(row, ft_answers[row_id])
        question = str(row["question"]).replace("|", "\\|")
        lines.append(
            f"| {row_id} | {row.get('category', '')} | {base_score.status} | {ft_score.status} | {question} |"
        )

    lines.extend(["", "## Side-by-side responses", ""])
    for row in rows:
        row_id = str(row["id"])
        lines.extend(
            [
                f"### {row_id} — {row.get('question', '')}",
                "",
                "**Base:**",
                "",
                base_answers[row_id],
                "",
                "**Fine-tuned:**",
                "",
                ft_answers[row_id],
                "",
                "---",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline base vs fine-tuned comparison")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--adapter-dir", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--prompts", type=Path, default=COMPARISON_PROMPTS)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--output", type=Path, default=LOG_DIR / "comparison-report.md")
    args = parser.parse_args()

    if not args.adapter_dir.exists():
        print(f"ERROR: adapter missing at {args.adapter_dir}", flush=True)
        return 1

    cfg = load_training_config(args.config)
    rows = load_eval_prompts(args.prompts)
    base_model = str(cfg["base_model"])
    max_seq = int(cfg["max_seq_length"])

    print(f"Loading base model: {base_model}", flush=True)
    base_model_obj, base_tok = load_inference_model(base_model, max_seq)
    base_answers = run_side(base_model_obj, base_tok, rows, max_new_tokens=args.max_new_tokens)
    del base_model_obj
    gc.collect()
    import torch

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print(f"Loading fine-tuned adapter: {args.adapter_dir}", flush=True)
    ft_model, ft_tok = load_inference_model(str(args.adapter_dir), max_seq)
    ft_answers = run_side(ft_model, ft_tok, rows, max_new_tokens=args.max_new_tokens)
    del ft_model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = args.output
    if output.name == "comparison-report.md":
        output = LOG_DIR / f"comparison-report-{timestamp}.md"

    write_report(output, rows, base_answers, ft_answers)
    print(f"Report written to {output}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
