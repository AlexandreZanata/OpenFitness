#!/usr/bin/env python3
"""Export merged model to GGUF q4_k_m via Unsloth (Phase 6 N-06-02)."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
os.environ.setdefault("UNSLOTH_USE_FP16", "1")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import (
    ADAPTER_DIR,
    ADAPTER_NAME,
    BASE_MODEL,
    GGUF_ALT_DIR,
    GGUF_DIR,
    GGUF_PATH,
    MAX_SEQ_LENGTH,
    MODELFILE_PATH,
)


def log(message: str) -> None:
    print(message, flush=True)


def find_gguf_output(*directories: Path) -> Path:
    for directory in directories:
        if not directory.exists():
            continue
        if GGUF_PATH.exists():
            return GGUF_PATH
        candidates = sorted(directory.glob("*.gguf"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0]
    raise FileNotFoundError(f"No GGUF file found under {[str(d) for d in directories]}")


def write_modelfile(gguf_path: Path) -> None:
    MODELFILE_PATH.write_text(
        f"""# NutriOffline Qwen2.5-3B ({ADAPTER_NAME})
FROM {gguf_path.name}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "<|im_start|>"
PARAMETER stop ""
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter-dir", type=Path, default=ADAPTER_DIR)
    parser.add_argument("--quantization", default="q4_k_m")
    args = parser.parse_args()

    import unsloth  # noqa: F401
    import torch
    from unsloth import FastLanguageModel

    if not args.adapter_dir.exists():
        log(f"FAIL: adapter missing at {args.adapter_dir}")
        return 1

    GGUF_DIR.mkdir(parents=True, exist_ok=True)

    log(f"Loading {args.adapter_dir} for GGUF export ({args.quantization})")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.adapter_dir),
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=torch.float16,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    log(f"Exporting GGUF to {GGUF_DIR} (this may take several minutes)...")
    model.save_pretrained_gguf(str(GGUF_DIR), tokenizer, quantization_method=args.quantization)

    gguf_source = find_gguf_output(GGUF_ALT_DIR, GGUF_DIR)
    GGUF_DIR.mkdir(parents=True, exist_ok=True)
    gguf_path = GGUF_PATH
    if gguf_source.resolve() != gguf_path.resolve():
        if gguf_path.exists():
            gguf_path.unlink()
        import shutil

        shutil.copy2(gguf_source, gguf_path)

    size_mb = gguf_path.stat().st_size / (1024 * 1024)
    metadata = {
        "adapter": ADAPTER_NAME,
        "base_model": BASE_MODEL,
        "quantization": args.quantization,
        "gguf_path": str(gguf_path),
        "size_mb": round(size_mb, 2),
        "exported_at": datetime.now(UTC).isoformat(),
    }
    (GGUF_DIR / "export_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    write_modelfile(gguf_path)

    gc.collect()
    log(f"PASS: GGUF export complete — {gguf_path} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
