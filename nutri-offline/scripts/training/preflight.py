#!/usr/bin/env python3
"""Phase 5 training preflight — CUDA, disk, dataset, token stats (no full train).

GIVEN Phase 4 dataset and config.yaml
WHEN preflight runs
THEN all acceptance checks pass before a multi-hour QLoRA run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import DEFAULT_CONFIG, LOG_DIR, ROOT, STATS_JSON
from config_loader import load_training_config
from dataset_loader import build_sft_dataset, load_jsonl_messages


def log(message: str) -> None:
    print(message, flush=True)


def check_cuda() -> tuple[bool, str]:
    import torch

    if not torch.cuda.is_available():
        return False, "CUDA not available"
    name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    return True, f"{name} ({vram_gb:.1f} GB VRAM)"


def check_disk(min_gb: float) -> tuple[bool, str]:
    usage = shutil.disk_usage(ROOT)
    free_gb = usage.free / (1024**3)
    if free_gb < min_gb:
        return False, f"free disk {free_gb:.1f} GB < required {min_gb} GB"
    return True, f"{free_gb:.1f} GB free under {ROOT}"


def check_writable(path: Path) -> tuple[bool, str]:
    path.mkdir(parents=True, exist_ok=True)
    probe = path / ".preflight_write"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return False, str(exc)
    return True, str(path)


def load_tokenizer_for_preflight(model_name: str):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)


def gate_passed(results: dict[str, bool]) -> bool:
    return all(results.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline Phase 5 training preflight")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "training-preflight.log"
    if log_path.exists():
        log_path.unlink()

    def write_log(message: str) -> None:
        log(message)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    write_log("NutriOffline Phase 5 training preflight")

    cfg = load_training_config(args.config, profile=args.profile)
    write_log(f"Profile: {cfg.get('_profile')}")

    results: dict[str, bool] = {}

    ok, detail = check_cuda()
    results["cuda"] = ok
    write_log(f"{'PASS' if ok else 'FAIL'}: cuda — {detail}")

    ok, detail = check_disk(float(cfg.get("min_free_disk_gb", 20)))
    results["disk"] = ok
    write_log(f"{'PASS' if ok else 'FAIL'}: disk — {detail}")

    train_path = Path(cfg["train_jsonl"])
    val_path = Path(cfg["val_jsonl"])
    results["train_jsonl"] = train_path.is_file()
    results["val_jsonl"] = val_path.is_file()
    write_log(f"{'PASS' if results['train_jsonl'] else 'FAIL'}: train_jsonl — {train_path}")
    write_log(f"{'PASS' if results['val_jsonl'] else 'FAIL'}: val_jsonl — {val_path}")

    if STATS_JSON.is_file():
        stats = json.loads(STATS_JSON.read_text(encoding="utf-8"))
        max_tok = int(stats.get("max_tokens_estimate", 0))
        max_seq = int(cfg["max_seq_length"])
        ok = max_tok <= max_seq
        results["stats_max_tokens"] = ok
        write_log(
            f"{'PASS' if ok else 'FAIL'}: stats max_tokens_estimate={max_tok} "
            f"<= max_seq_length={max_seq}"
        )
    else:
        results["stats_max_tokens"] = False
        write_log(f"FAIL: missing {STATS_JSON}")

    train_count = len(load_jsonl_messages(train_path)) if train_path.is_file() else 0
    val_count = len(load_jsonl_messages(val_path)) if val_path.is_file() else 0
    results["min_train_count"] = train_count >= int(cfg.get("min_train_examples", 2000))
    results["min_val_count"] = val_count >= int(cfg.get("min_val_examples", 200))
    write_log(
        f"{'PASS' if results['min_train_count'] else 'FAIL'}: train count {train_count}"
    )
    write_log(f"{'PASS' if results['min_val_count'] else 'FAIL'}: val count {val_count}")

    output_dir = Path(cfg["output_dir"])
    ok, detail = check_writable(output_dir.parent)
    results["output_writable"] = ok
    write_log(f"{'PASS' if ok else 'FAIL'}: output parent writable — {detail}")

    if results.get("cuda") and train_path.is_file():
        try:
            tokenizer = load_tokenizer_for_preflight(cfg["base_model"])
            train_ds, train_stats = build_sft_dataset(
                train_path,
                tokenizer,
                max_seq_length=int(cfg["max_seq_length"]),
            )
            val_ds, val_stats = build_sft_dataset(
                val_path,
                tokenizer,
                max_seq_length=int(cfg["max_seq_length"]),
            )
            results["tokenize_train"] = len(train_ds) > 0
            results["tokenize_val"] = len(val_ds) > 0
            results["system_prompt_aligned"] = int(train_stats["system_prompt_mismatches"]) == 0
            write_log(
                f"PASS: tokenize train kept={train_stats['kept_examples']} "
                f"dropped={train_stats['dropped_over_max_seq']} "
                f"max_tok={train_stats['max_token_length']}"
            )
            write_log(
                f"PASS: tokenize val kept={val_stats['kept_examples']} "
                f"max_tok={val_stats['max_token_length']}"
            )
            write_log(
                f"{'PASS' if results['system_prompt_aligned'] else 'FAIL'}: "
                f"system prompt mismatches={train_stats['system_prompt_mismatches']}"
            )
        except Exception as exc:
            results["tokenize_train"] = False
            results["tokenize_val"] = False
            results["system_prompt_aligned"] = False
            write_log(f"FAIL: tokenization — {exc}")

    passed = gate_passed(results)
    write_log(f"{'PASS' if passed else 'FAIL'}: training preflight gate")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
