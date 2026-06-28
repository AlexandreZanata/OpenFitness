#!/usr/bin/env python3
"""Phase 0 environment validation — run manually after setup.

GIVEN a Pop!_OS machine with NVIDIA drivers
WHEN this script runs inside `.local/nutri-offline/venv`
THEN GPU, PyTorch CUDA, Unsloth, and DuckDB checks pass
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_VRAM_MIB = 7500


def check_gpu() -> None:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.free",
            "--format=csv,noheader",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    line = result.stdout.strip().splitlines()[0]
    name, total, free = [part.strip() for part in line.split(",")]
    total_mib = int(total.replace(" MiB", ""))
    free_mib = int(free.replace(" MiB", ""))
    print(f"GPU: {name}")
    print(f"VRAM total: {total_mib} MiB, free: {free_mib} MiB")
    if total_mib < MIN_VRAM_MIB:
        raise SystemExit(f"FAIL: expected >= {MIN_VRAM_MIB} MiB VRAM, got {total_mib}")


def check_torch_cuda() -> None:
    import torch

    if not torch.cuda.is_available():
        raise SystemExit("FAIL: torch.cuda.is_available() is False")
    device = torch.cuda.get_device_name(0)
    print(f"PyTorch {torch.__version__} — CUDA device: {device}")


def check_unsloth() -> None:
    from unsloth import FastLanguageModel  # noqa: F401

    print("Unsloth import OK")


def check_duckdb() -> None:
    import duckdb

    value = duckdb.connect(":memory:").execute("SELECT 42").fetchone()[0]
    if value != 42:
        raise SystemExit("FAIL: DuckDB sanity query failed")
    print("DuckDB OK")


def main() -> int:
    print(f"NutriOffline environment check — root: {ROOT}")
    check_gpu()
    check_torch_cuda()
    check_unsloth()
    check_duckdb()
    print("PASS: all Phase 0 environment checks succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
