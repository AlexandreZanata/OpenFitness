#!/usr/bin/env python3
"""Phase 5 orchestrator — preflight then optional QLoRA training."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
ROOT = TRAINING_DIR.parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline Phase 5 training pipeline")
    parser.add_argument("--config", type=Path, default=TRAINING_DIR / "config.yaml")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Run preflight only")
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    preflight_cmd = [
        sys.executable,
        str(TRAINING_DIR / "preflight.py"),
        "--config",
        str(args.config),
    ]
    if args.profile:
        preflight_cmd.extend(["--profile", args.profile])

    result = subprocess.run(preflight_cmd, cwd=ROOT, check=False)
    if result.returncode != 0:
        return result.returncode

    if args.dry_run:
        print("PASS: dry-run — preflight only", flush=True)
        return 0

    train_cmd = [
        sys.executable,
        str(TRAINING_DIR / "train_qlora.py"),
        "--config",
        str(args.config),
    ]
    if args.profile:
        train_cmd.extend(["--profile", args.profile])
    if args.max_steps is not None:
        train_cmd.extend(["--max-steps", str(args.max_steps)])

    return subprocess.run(train_cmd, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
