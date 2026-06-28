#!/usr/bin/env python3
"""Orchestrate Phase 2 normalization pipeline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "parse_taco.py",
    "parse_fdc.py",
    "parse_off.py",
    "merge.py",
    "build_duckdb.py",
    "validate.py",
]


def main() -> int:
    here = Path(__file__).resolve().parent
    for script in SCRIPTS:
        path = here / script
        print(f"\n=== {script} ===", flush=True)
        result = subprocess.run([sys.executable, str(path)], check=False)
        if result.returncode != 0:
            return result.returncode
    print("\nPASS: normalization pipeline complete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
