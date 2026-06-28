#!/usr/bin/env python3
"""Merge LoRA adapter into base weights (Phase 6 N-06-01)."""

from __future__ import annotations

import argparse
import gc
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
os.environ.setdefault("UNSLOTH_USE_FP16", "1")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import ADAPTER_DIR, BASE_MODEL, MAX_SEQ_LENGTH, MERGED_DIR


def log(message: str) -> None:
    print(message, flush=True)


def load_model_and_tokenizer(adapter_dir: Path):
    import unsloth  # noqa: F401
    import torch
    from unsloth import FastLanguageModel

    if not adapter_dir.exists():
        raise FileNotFoundError(f"Adapter missing at {adapter_dir}")

    log(f"Loading base {BASE_MODEL} with adapter {adapter_dir}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(adapter_dir),
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=torch.float16,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def smoke_generate(model, tokenizer) -> str:
    import torch

    messages = [
        {"role": "system", "content": "You are a nutrition assistant."},
        {"role": "user", "content": "Quantas calorias tem arroz cozido por 100g?"},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=64, use_cache=True)
    text = tokenizer.decode(outputs[0], skip_special_tokens=False)
    return text[-200:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-dir", type=Path, default=ADAPTER_DIR)
    parser.add_argument("--output", type=Path, default=MERGED_DIR)
    args = parser.parse_args()

    model, tokenizer = load_model_and_tokenizer(args.adapter_dir)

    sample = smoke_generate(model, tokenizer)
    log(f"Pre-merge generation sample: ...{sample[-120:]}")

    args.output.mkdir(parents=True, exist_ok=True)
    log(f"Merging LoRA -> {args.output}")
    model.save_pretrained_merged(str(args.output), tokenizer, save_method="merged_16bit")

    tokenizer.save_pretrained(str(args.output))
    gc.collect()

    log(f"PASS: merged model saved to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
