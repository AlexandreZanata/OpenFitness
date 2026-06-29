#!/usr/bin/env python3
"""Export bge-small-en-v1.5 to ONNX int8 for mobile runtime (N-08-09)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mobile_paths import EMBEDDER_ONNX, LOG_DIR, MOBILE_EMBED_DIM, MOBILE_EMBED_MODEL, MOBILE_INDEX_DIR, ROOT  # noqa: E402
from pack_budget import EMBEDDER_MAX_BYTES, validate_component_budget  # noqa: E402


def export_onnx(
    *,
    output_path: Path,
    model_name: str = MOBILE_EMBED_MODEL,
    quantize: bool = True,
) -> dict:
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer

    os.environ.setdefault("HF_HOME", str(ROOT / "models" / "base"))
    model = SentenceTransformer(model_name, device="cpu")
    transformer = model[0].auto_model.to("cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    transformer.eval()

    dummy = tokenizer(
        ["nutrition embedding export"],
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    class PoolingWrapper(torch.nn.Module):
        def __init__(self, inner: torch.nn.Module) -> None:
            super().__init__()
            self.inner = inner

        def forward(self, input_ids, attention_mask):  # type: ignore[no-untyped-def]
            outputs = self.inner(input_ids=input_ids, attention_mask=attention_mask)
            token_embeddings = outputs.last_hidden_state
            mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            summed = torch.sum(token_embeddings * mask, dim=1)
            counts = torch.clamp(mask.sum(dim=1), min=1e-9)
            pooled = summed / counts
            return torch.nn.functional.normalize(pooled, p=2, dim=1)

    wrapper = PoolingWrapper(transformer)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fp32_path = output_path.with_suffix(".fp32.onnx")
    torch.onnx.export(
        wrapper,
        (dummy["input_ids"], dummy["attention_mask"]),
        str(fp32_path),
        input_names=["input_ids", "attention_mask"],
        output_names=["sentence_embedding"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "sentence_embedding": {0: "batch"},
        },
        opset_version=17,
    )

    if quantize:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        quantize_dynamic(
            str(fp32_path),
            str(output_path),
            weight_type=QuantType.QInt8,
        )
        fp32_path.unlink(missing_ok=True)
    else:
        fp32_path.rename(output_path)

    size_bytes = output_path.stat().st_size
    validate_component_budget("embedder", size_bytes)
    return {
        "model_id": model_name,
        "dims": MOBILE_EMBED_DIM,
        "format": "onnx-int8",
        "size_bytes": size_bytes,
        "output": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export mobile embedder ONNX")
    parser.add_argument("--output", type=Path, default=EMBEDDER_ONNX)
    parser.add_argument("--no-quantize", action="store_true")
    args = parser.parse_args()

    try:
        summary = export_onnx(
            output_path=args.output,
            quantize=not args.no_quantize,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if summary["size_bytes"] > EMBEDDER_MAX_BYTES:
        print(
            f"WARN: embedder {summary['size_bytes']} bytes exceeds {EMBEDDER_MAX_BYTES}",
            file=sys.stderr,
        )

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    MOBILE_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "mobile-embedder-export.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
