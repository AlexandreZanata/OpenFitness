#!/usr/bin/env python3
"""Phase 5/11 domain evaluation — curated prompt suite with optional production RAG path."""

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
APP_DIR = TRAINING_DIR.parent / "app"
RAG_DIR = TRAINING_DIR.parent / "rag"
DATASET_DIR = TRAINING_DIR.parent / "dataset"


def _load_module(name: str, path: Path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Register rag `_paths` before app/RAG imports so embed.py resolves correctly.
_rag_paths = _load_module("nutri_rag_paths", RAG_DIR / "_paths.py")
sys.modules["_paths"] = _rag_paths
_training_paths = _load_module("nutri_training_paths", TRAINING_DIR / "_paths.py")

DEFAULT_ADAPTER = _training_paths.DEFAULT_ADAPTER
DEFAULT_CONFIG = _training_paths.DEFAULT_CONFIG
FIXTURE_ALIASES = _training_paths.FIXTURE_ALIASES
LOG_DIR = _training_paths.LOG_DIR
ROOT = _training_paths.ROOT

sys.path.insert(0, str(RAG_DIR))
sys.path.insert(0, str(TRAINING_DIR))
sys.path.insert(0, str(APP_DIR))

from config_loader import load_training_config  # noqa: E402

sys.path.insert(0, str(DATASET_DIR))
from constants import SYSTEM_PROMPT  # noqa: E402
from eval_scoring import (  # noqa: E402
    PASS_THRESHOLDS,
    PASS_THRESHOLDS_V2,
    ScoredRow,
    aggregate_metrics,
    load_eval_prompts,
    score_row,
)
from training_metrics import check_loss_stable, find_latest_training_run, load_training_run  # noqa: E402

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


def run_eval_llm(
    rows: list[dict[str, Any]],
    *,
    adapter_dir: Path,
    base_model: str,
    max_seq_length: int,
    max_new_tokens: int,
) -> list[tuple[ScoredRow, list[dict[str, str]]]]:
    model, tokenizer = load_model(adapter_dir, base_model, max_seq_length)
    scored: list[tuple[ScoredRow, list[dict[str, str]]]] = []
    try:
        for index, row in enumerate(rows, start=1):
            messages = build_messages(row)
            answer = generate_answer(model, tokenizer, messages, max_new_tokens=max_new_tokens)
            result = score_row(row, answer)
            scored.append((result, []))
            print(f"[{index}/{len(rows)}] {result.id} {result.status}: {result.detail}", flush=True)
    finally:
        del model
        gc.collect()
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return scored


def run_eval_production_rag(rows: list[dict[str, Any]]) -> list[tuple[ScoredRow, list[dict[str, str]]]]:
    from orchestrator import NutriAssistant  # noqa: E402

    assistant = NutriAssistant()
    scored: list[tuple[ScoredRow, list[dict[str, str]]]] = []
    for index, row in enumerate(rows, start=1):
        response = assistant.ask(str(row["question"]), use_rag=True, mode="auto")
        result = score_row(row, response.answer, sources=response.sources)
        scored.append((result, response.sources))
        print(
            f"[{index}/{len(rows)}] {result.id} {result.status} mode={response.mode}: {result.detail}",
            flush=True,
        )
    return scored


def scored_to_dict(scored: ScoredRow, sources: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "id": scored.id,
        "category": scored.category,
        "status": scored.status,
        "detail": scored.detail,
        "question": scored.question,
        "answer": scored.answer,
        "sources": sources,
    }


def resolve_fixture_path(args: argparse.Namespace) -> Path:
    if args.prompts is not None:
        return args.prompts
    alias = args.fixture
    if alias not in FIXTURE_ALIASES:
        raise SystemExit(f"Unknown --fixture {alias!r}; choose from {list(FIXTURE_ALIASES)}")
    return FIXTURE_ALIASES[alias]


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline domain evaluation")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--adapter-dir", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--prompts", type=Path, default=None)
    parser.add_argument(
        "--fixture",
        choices=sorted(FIXTURE_ALIASES),
        default="v1",
        help="Fixture alias when --prompts omitted",
    )
    parser.add_argument("--max-prompts", type=int, default=None, help="Limit prompts (gate/ci profile)")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--skip-training-check", action="store_true")
    parser.add_argument(
        "--require-rag",
        action="store_true",
        help="Use production NutriAssistant + LanceDB (Phase 11 G-DOM)",
    )
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="Score pre-recorded responses JSON (no GPU)",
    )
    parser.add_argument("--responses-json", type=Path, default=None)
    parser.add_argument("--report-md", type=Path, default=None, help="Write markdown summary (N-11-24)")
    args = parser.parse_args()

    cfg = load_training_config(args.config)
    prompts_path = resolve_fixture_path(args)
    rows = load_eval_prompts(prompts_path)
    if args.max_prompts is not None:
        rows = rows[: args.max_prompts]

    use_v2_thresholds = args.fixture in {"v2", "gate-v2"} or "domain_eval_v2" in prompts_path.name
    thresholds = PASS_THRESHOLDS_V2 if use_v2_thresholds else PASS_THRESHOLDS

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = LOG_DIR / f"eval-domain-{timestamp}.json"

    training_check: dict[str, Any] | None = None
    if not args.skip_training_check and not args.require_rag:
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

    if args.score_only:
        if args.responses_json is None:
            print("ERROR: --score-only requires --responses-json", flush=True)
            return 1
        responses = json.loads(args.responses_json.read_text(encoding="utf-8"))
        by_id = {entry["id"]: entry for entry in responses}
        scored_pairs = [
            (
                score_row(row, by_id[row["id"]]["answer"], sources=by_id[row["id"]].get("sources")),
                by_id[row["id"]].get("sources", []),
            )
            for row in rows
            if row["id"] in by_id
        ]
    elif args.require_rag:
        scored_pairs = run_eval_production_rag(rows)
    else:
        if not args.adapter_dir.exists():
            print(f"ERROR: adapter missing at {args.adapter_dir}", flush=True)
            return 1
        scored_pairs = run_eval_llm(
            rows,
            adapter_dir=args.adapter_dir,
            base_model=str(cfg["base_model"]),
            max_seq_length=int(cfg["max_seq_length"]),
            max_new_tokens=args.max_new_tokens,
        )

    scored = [pair[0] for pair in scored_pairs]
    metrics = aggregate_metrics(scored, rows, thresholds=thresholds)
    report = {
        "timestamp": timestamp,
        "adapter_dir": str(args.adapter_dir),
        "prompts_file": str(prompts_path),
        "prompt_count": len(rows),
        "require_rag": args.require_rag,
        "metrics": metrics,
        "training_check": training_check,
        "results": [scored_to_dict(row, sources) for row, sources in scored_pairs],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report: {output_path}", flush=True)
    print(
        f"Row pass {metrics.get('row_pass_pct', metrics['format_compliance_pct'])}% | "
        f"Hallucination {metrics['hallucination_false_fact_pct']}% | "
        f"Gate: {'PASS' if metrics['pass'] else 'FAIL'}",
        flush=True,
    )

    if args.report_md:
        write_markdown_report(args.report_md, report)

    if training_check is not None and not training_check.get("pass", True):
        return 1
    return 0 if metrics["pass"] else 1


def write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    metrics = report["metrics"]
    failures = [row for row in report["results"] if row["status"] == "FAIL"]
    lines = [
        "# Domain eval benchmark report",
        "",
        f"- **Timestamp:** {report['timestamp']}",
        f"- **Prompts:** {report['prompt_count']} ({report['prompts_file']})",
        f"- **Production RAG:** {report.get('require_rag')}",
        f"- **Row pass:** {metrics.get('row_pass_pct')}%",
        f"- **Hallucination false facts:** {metrics['hallucination_false_fact_pct']}%",
        f"- **Gate:** {'PASS' if metrics['pass'] else 'FAIL'}",
        "",
        "## Failures",
        "",
    ]
    if not failures:
        lines.append("_None_")
    else:
        for row in failures[:30]:
            lines.append(f"- **{row['id']}** ({row['category']}): {row['detail']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Markdown report: {path}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
