#!/usr/bin/env python3
"""Phase 5 domain evaluation — curated prompt suite on fine-tuned adapter.

GIVEN nutri-qwen25-3b-v1 adapter and domain_eval_prompts.jsonl
WHEN eval_domain runs
THEN metrics JSON is written and pass/fail gate is reported
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

TRAINING_DIR = Path(__file__).resolve().parent
DATASET_DIR = TRAINING_DIR.parent / "dataset"
sys.path.insert(0, str(TRAINING_DIR))

from _paths import DEFAULT_ADAPTER, DEFAULT_CONFIG, EVAL_PROMPTS, LOG_DIR, ROOT
from config_loader import load_training_config

sys.path.insert(0, str(DATASET_DIR))
from constants import SYSTEM_PROMPT
from eval_scoring import ScoredRow, aggregate_metrics, load_eval_prompts, score_row
from training_metrics import check_loss_stable, find_latest_training_run, load_training_run

os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
os.environ.setdefault("UNSLOTH_USE_FP16", "1")


def build_messages(row: dict[str, Any]) -> list[dict[str, str]]:
    system = SYSTEM_PROMPT
    rag_context = row.get("rag_context")
    if rag_context:
        system = f"{SYSTEM_PROMPT}\n\nContext (use estes valores com precisão):\n{rag_context}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": str(row["question"])},
    ]


def generate_answer(model, tokenizer, messages: list[dict[str, str]], *, max_new_tokens: int) -> str:
    import torch

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            temperature=0.1,
            do_sample=False,
        )
    generated = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    return generated.strip()


def load_model(adapter_dir: Path, base_model: str, max_seq_length: int):
    import unsloth  # noqa: F401
    import torch
    from unsloth import FastLanguageModel

    model_name = str(adapter_dir) if adapter_dir.exists() else base_model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=torch.float16,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def run_eval(
    rows: list[dict[str, Any]],
    *,
    adapter_dir: Path,
    base_model: str,
    max_seq_length: int,
    max_new_tokens: int,
) -> list[ScoredRow]:
    model, tokenizer = load_model(adapter_dir, base_model, max_seq_length)
    scored: list[ScoredRow] = []
    try:
        for index, row in enumerate(rows, start=1):
            messages = build_messages(row)
            answer = generate_answer(model, tokenizer, messages, max_new_tokens=max_new_tokens)
            result = score_row(row, answer)
            scored.append(result)
            print(f"[{index}/{len(rows)}] {result.id} {result.status}: {result.detail}", flush=True)
    finally:
        del model
        gc.collect()
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return scored


def scored_to_dict(scored: ScoredRow) -> dict[str, str]:
    return {
        "id": scored.id,
        "category": scored.category,
        "status": scored.status,
        "detail": scored.detail,
        "question": scored.question,
        "answer": scored.answer,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline Phase 5 domain evaluation")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--adapter-dir", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--prompts", type=Path, default=EVAL_PROMPTS)
    parser.add_argument("--max-prompts", type=int, default=None, help="Limit prompts (gate/ci profile)")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--skip-training-check", action="store_true")
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="Score pre-recorded responses JSON (no GPU)",
    )
    parser.add_argument("--responses-json", type=Path, default=None)
    args = parser.parse_args()

    cfg = load_training_config(args.config)
    rows = load_eval_prompts(args.prompts)
    if args.max_prompts is not None:
        rows = rows[: args.max_prompts]

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = LOG_DIR / f"eval-domain-{timestamp}.json"

    training_check: dict[str, Any] | None = None
    if not args.skip_training_check:
        run_path = find_latest_training_run(LOG_DIR)
        if run_path is None:
            print("WARN: no full training-run JSON found — skipping loss stability check", flush=True)
        else:
            payload = load_training_run(run_path)
            training_check = {
                "training_run": str(run_path),
                **check_loss_stable(payload.get("history", [])),
            }
            print(f"Training loss check: {'PASS' if training_check['pass'] else 'FAIL'}", flush=True)
            if not training_check["pass"]:
                print(f"  reasons: {training_check.get('reasons')}", flush=True)

    if args.score_only:
        if args.responses_json is None:
            print("ERROR: --score-only requires --responses-json", flush=True)
            return 1
        responses = json.loads(args.responses_json.read_text(encoding="utf-8"))
        by_id = {entry["id"]: entry["answer"] for entry in responses}
        scored = [score_row(row, by_id[row["id"]]) for row in rows if row["id"] in by_id]
    else:
        if not args.adapter_dir.exists():
            print(f"ERROR: adapter missing at {args.adapter_dir}", flush=True)
            return 1
        scored = run_eval(
            rows,
            adapter_dir=args.adapter_dir,
            base_model=str(cfg["base_model"]),
            max_seq_length=int(cfg["max_seq_length"]),
            max_new_tokens=args.max_new_tokens,
        )

    metrics = aggregate_metrics(scored, rows)
    report = {
        "timestamp": timestamp,
        "adapter_dir": str(args.adapter_dir),
        "prompts_file": str(args.prompts),
        "prompt_count": len(rows),
        "metrics": metrics,
        "training_check": training_check,
        "results": [scored_to_dict(row) for row in scored],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report: {output_path}", flush=True)
    print(
        f"Format {metrics['format_compliance_pct']}% | "
        f"Hallucination {metrics['hallucination_false_fact_pct']}% | "
        f"RAG {metrics['rag_fidelity_pct']}% | "
        f"Gate: {'PASS' if metrics['pass'] else 'FAIL'}",
        flush=True,
    )

    if training_check is not None and not training_check.get("pass", True):
        return 1
    return 0 if metrics["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
