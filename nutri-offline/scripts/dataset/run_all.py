#!/usr/bin/env python3
"""Orchestrate Phase 4 fine-tuning dataset generation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-generate", action="store_true")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    steps: list[list[str]] = []

    if not args.skip_generate:
        steps.append(
            [
                sys.executable,
                str(here / "generate.py"),
                "--target",
                str(args.target),
                "--seed",
                str(args.seed),
            ]
        )

    steps.extend(
        [
            [sys.executable, str(here / "split.py"), "--seed", str(args.seed)],
            [sys.executable, str(here / "stats.py")],
            [sys.executable, str(here / "validate.py")],
        ]
    )

    for command in steps:
        print(f"\n=== {' '.join(command[-2:])} ===", flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            return result.returncode

    print("\nPASS: Phase 4 fine-tuning dataset pipeline complete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
