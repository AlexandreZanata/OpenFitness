#!/usr/bin/env python3
"""Phase 0 Unsloth smoke train — 10 steps on Qwen2.5-3B-Instruct (4-bit QLoRA).

GIVEN RTX 4060 8 GB and an activated venv
WHEN this script runs
THEN training completes without OOM and peak VRAM stays <= 7.5 GB
"""

from __future__ import annotations

import gc
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
os.environ.setdefault("UNSLOTH_USE_FP16", "1")

MAX_VRAM_GB = 7.5
MODEL_NAME = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit"
ADAPTER_DIR = ROOT / "models" / "adapters" / "smoke-test"
LOG_PATH = ROOT / "logs" / "smoke-train.log"


def log(message: str) -> None:
    print(message, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def peak_vram_gb() -> float:
    import torch

    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_allocated() / (1024**3)


def build_dataset():
    from datasets import Dataset

    examples = [
        {
            "text": (
                "<|im_start|>system\nYou are a nutrition assistant.\n"
                "<|im_start|>user\nCalories in 100 g cooked white rice?\n"
                "<|im_start|>assistant\nAbout 130 kcal per 100 g cooked white rice."
            )
        },
        {
            "text": (
                "<|im_start|>system\nYou are a nutrition assistant.\n"
                "<|im_start|>user\nProtein in 1 boiled egg?\n"
                "<|im_start|>assistant\nAbout 6 g protein in one medium boiled egg."
            )
        },
        {
            "text": (
                "<|im_start|>system\nYou are a nutrition assistant.\n"
                "<|im_start|>user\nIs banana a good pre-workout snack?\n"
                "<|im_start|>assistant\nYes — quick carbs and potassium support short workouts."
            )
        },
    ]
    return Dataset.from_list(examples)


def main() -> int:
    import unsloth  # noqa: F401 — must import before trl/transformers

    import torch
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel

    if LOG_PATH.exists():
        LOG_PATH.unlink()

    log("NutriOffline smoke train — Phase 0")
    log(f"Model: {MODEL_NAME}")
    log(f"HF_HOME: {os.environ['HF_HOME']}")

    if not torch.cuda.is_available():
        log("FAIL: CUDA not available")
        return 1

    torch.cuda.reset_peak_memory_stats()
    gc.collect()
    torch.cuda.empty_cache()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=512,
        dtype=torch.float16,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    dataset = build_dataset()

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=SFTConfig(
            output_dir=str(ADAPTER_DIR),
            max_steps=10,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            fp16=True,
            bf16=False,
            logging_steps=1,
            save_strategy="no",
            optim="paged_adamw_8bit",
            report_to="none",
            seed=42,
            dataset_text_field="text",
        ),
    )

    log("Starting 10-step smoke train...")
    trainer.train()

    peak = peak_vram_gb()
    log(f"Peak VRAM: {peak:.2f} GB")

    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(ADAPTER_DIR))
    tokenizer.save_pretrained(str(ADAPTER_DIR))
    log(f"Adapter saved to {ADAPTER_DIR}")

    if peak > MAX_VRAM_GB:
        log(f"FAIL: peak VRAM {peak:.2f} GB exceeds limit {MAX_VRAM_GB} GB")
        return 1

    log("PASS: smoke train completed without OOM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
