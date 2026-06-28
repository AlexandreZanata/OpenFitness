#!/usr/bin/env python3
"""Orchestrate RAG V2 index build (aliases + v2 LanceDB + golden tests)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["v1", "all"], default="v1")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--skip-build", action="store_true", help="Skip index rebuild")
    parser.add_argument("--skip-aliases", action="store_true", help="Skip alias parquet build")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    root = here.parents[1]
    steps: list[list[str]] = []

    if not args.skip_aliases:
        steps.append([sys.executable, str(here / "build_food_aliases.py")])

    if not args.skip_build:
        steps.append(
            [
                sys.executable,
                str(here / "build_index_v2.py"),
                "--scope",
                args.scope,
                "--device",
                args.device,
            ]
        )

    steps.append(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_food_aliases",
            "tests.test_hybrid_search",
            "tests.test_lookup_golden",
            "-v",
        ]
    )

    for command in steps:
        print(f"\n=== {' '.join(command[-3:])} ===", flush=True)
        result = subprocess.run(command, check=False, cwd=str(root))
        if result.returncode != 0:
            return result.returncode

    print("\nPASS: RAG V2 Phase B pipeline complete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
