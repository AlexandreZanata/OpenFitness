#!/usr/bin/env python3
"""Phase 5 QLoRA SFT training — Unsloth + TRL on Phase 4 ChatML dataset.

GIVEN RTX 4060 8 GB, Phase 4 train/val JSONL, and config.yaml
WHEN train_qlora runs
THEN LoRA adapter is saved and training metrics are logged
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import DEFAULT_CONFIG, LOG_DIR, ROOT
from config_loader import load_training_config
from dataset_loader import build_sft_dataset

os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
os.environ.setdefault("UNSLOTH_USE_FP16", "1")


def log(message: str, log_path: Path) -> None:
    print(message, flush=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def peak_vram_gb() -> float:
    import torch

    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_allocated() / (1024**3)


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline Phase 5 QLoRA training")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    cfg = load_training_config(args.config, profile=args.profile)
    if args.max_steps is not None:
        cfg["max_steps"] = args.max_steps

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_log = LOG_DIR / f"training-run-{timestamp}.log"
    metrics_path = LOG_DIR / f"training-run-{timestamp}.json"

    if run_log.exists():
        run_log.unlink()

    log("NutriOffline Phase 5 QLoRA training", run_log)
    log(f"Profile: {cfg.get('_profile')}", run_log)
    log(f"Base model: {cfg['base_model']}", run_log)

    import unsloth  # noqa: F401 — must import before trl/transformers

    import torch
    from transformers import EarlyStoppingCallback
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel

    if not torch.cuda.is_available():
        log("FAIL: CUDA not available", run_log)
        return 1

    torch.cuda.reset_peak_memory_stats()
    gc.collect()
    torch.cuda.empty_cache()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg["base_model"],
        max_seq_length=int(cfg["max_seq_length"]),
        dtype=torch.float16,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=int(cfg["lora_r"]),
        target_modules=list(cfg["lora_target_modules"]),
        lora_alpha=int(cfg["lora_alpha"]),
        lora_dropout=float(cfg.get("lora_dropout", 0.0)),
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=int(cfg.get("seed", 42)),
    )

    train_ds, train_stats = build_sft_dataset(
        Path(cfg["train_jsonl"]),
        tokenizer,
        max_seq_length=int(cfg["max_seq_length"]),
    )
    val_ds, val_stats = build_sft_dataset(
        Path(cfg["val_jsonl"]),
        tokenizer,
        max_seq_length=int(cfg["max_seq_length"]),
    )

    log(
        f"Train: kept={train_stats['kept_examples']} dropped={train_stats['dropped_over_max_seq']}",
        run_log,
    )
    log(f"Val: kept={val_stats['kept_examples']}", run_log)

    if train_stats["kept_examples"] == 0:
        log("FAIL: no training examples after length filter", run_log)
        return 1

    output_dir = Path(cfg["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    max_steps = cfg.get("max_steps")
    has_max_steps = max_steps is not None and int(max_steps) > 0
    eval_enabled = len(val_ds) > 0 and not has_max_steps

    sft_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=float(cfg.get("num_train_epochs", 3)),
        max_steps=int(max_steps) if has_max_steps else -1,
        per_device_train_batch_size=int(cfg["per_device_train_batch_size"]),
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=int(cfg["gradient_accumulation_steps"]),
        learning_rate=float(cfg["learning_rate"]),
        fp16=bool(cfg.get("fp16", True)),
        bf16=bool(cfg.get("bf16", False)),
        warmup_ratio=float(cfg.get("warmup_ratio", 0.05)),
        weight_decay=float(cfg.get("weight_decay", 0.01)),
        lr_scheduler_type=str(cfg.get("lr_scheduler", "cosine")),
        logging_steps=int(cfg.get("logging_steps", 10)),
        eval_strategy="steps" if eval_enabled else "no",
        eval_steps=int(cfg.get("eval_steps", 100)) if eval_enabled else None,
        save_strategy="no" if has_max_steps else "steps",
        save_steps=int(cfg.get("save_steps", 100)),
        load_best_model_at_end=eval_enabled,
        metric_for_best_model="eval_loss" if eval_enabled else None,
        greater_is_better=False if eval_enabled else None,
        optim="paged_adamw_8bit",
        seed=int(cfg.get("seed", 42)),
        report_to="none",
        dataset_text_field="text",
    )

    callbacks = []
    patience = int(cfg.get("early_stopping_patience", 0))
    if eval_enabled and patience > 0:
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=patience))

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds if eval_enabled else None,
        args=sft_args,
        callbacks=callbacks,
    )

    log("Starting training...", run_log)
    trainer.train()

    peak = peak_vram_gb()
    log(f"Peak VRAM: {peak:.2f} GB", run_log)

    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    log(f"Adapter saved to {output_dir}", run_log)

    payload = {
        "timestamp": timestamp,
        "profile": cfg.get("_profile"),
        "config": {k: v for k, v in cfg.items() if not k.startswith("_")},
        "train_stats": train_stats,
        "val_stats": val_stats,
        "peak_vram_gb": round(peak, 3),
        "history": trainer.state.log_history,
    }
    metrics_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"Metrics saved to {metrics_path}", run_log)

    max_vram = float(cfg.get("max_vram_gb", 7.5))
    if peak > max_vram:
        log(f"FAIL: peak VRAM {peak:.2f} GB exceeds limit {max_vram} GB", run_log)
        return 1

    log("PASS: training completed", run_log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
