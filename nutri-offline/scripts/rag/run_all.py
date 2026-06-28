#!/usr/bin/env python3
"""Orchestrate Phase 3 RAG index build and validation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["v1", "all"], default="v1")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    steps: list[list[str]] = []
    if not args.skip_build:
        steps.append(
            [
                sys.executable,
                str(here / "build_index.py"),
                "--scope",
                args.scope,
                "--device",
                args.device,
            ]
        )
    steps.extend(
        [
            [sys.executable, str(here / "test_queries.py")],
        ]
    )

    for command in steps:
        print(f"\n=== {' '.join(command[-2:])} ===", flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            return result.returncode

    print("\nPASS: Phase 3 RAG pipeline complete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
