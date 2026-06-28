#!/usr/bin/env python3
"""Orchestrate Phase 1 raw data downloads."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "fetch_taco.py",
    "fetch_taco_community.py",
    "fetch_fdc_bulk.py",
    "fetch_openfoodfacts.py",
    "fetch_tbca.py",
]


def main() -> int:
    here = Path(__file__).resolve().parent
    for script in SCRIPTS:
        path = here / script
        print(f"\n=== Running {script} ===", flush=True)
        result = subprocess.run([sys.executable, str(path)], check=False)
        if result.returncode != 0:
            print(f"ERROR: {script} failed with code {result.returncode}", flush=True)
            return result.returncode
    print("\nPASS: all download scripts completed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
