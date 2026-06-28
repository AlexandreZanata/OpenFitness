#!/usr/bin/env python3
"""Orchestrate Phase 6 export: merge (optional) + GGUF."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-merge", action="store_true", help="GGUF export merges internally")
    parser.add_argument("--adapter-dir", default="")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    extra: list[str] = []
    if args.adapter_dir:
        extra = ["--adapter-dir", args.adapter_dir]

    steps: list[list[str]] = []
    if not args.skip_merge:
        steps.append([sys.executable, str(here / "merge_lora.py"), *extra])
    steps.append([sys.executable, str(here / "export_gguf.py"), *extra])

    for command in steps:
        print(f"\n=== {' '.join(command[-2:])} ===", flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            return result.returncode

    print("\nPASS: Phase 6 export pipeline complete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
