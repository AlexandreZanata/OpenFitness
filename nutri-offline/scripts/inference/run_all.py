#!/usr/bin/env python3
"""Orchestrate Phase 6: build llama.cpp, export GGUF, inference tests."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--skip-build", action="store_true", help="Skip llama.cpp cmake build")
    parser.add_argument("--adapter", default=os.environ.get("NUTRI_ADAPTER", "smoke-test"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    export = root / "scripts" / "export"
    inference = root / "scripts" / "inference"
    env = os.environ.copy()
    env["NUTRI_ADAPTER"] = args.adapter
    env.setdefault("HF_HOME", str(root / "models" / "base"))
    env.setdefault("UNSLOTH_USE_FP16", "1")

    if not args.skip_export:
        result = subprocess.run(
            [sys.executable, str(export / "run_all.py"), "--skip-merge"],
            env=env,
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    if not args.skip_build:
        result = subprocess.run(["bash", str(inference / "build_llama_cpp.sh")], check=False)
        if result.returncode != 0:
            return result.returncode

    gguf_dir = root / "models" / "gguf"
    ggufs = list(gguf_dir.glob("*.gguf"))
    if not ggufs:
        print("FAIL: no GGUF file found", flush=True)
        return 1
    env["NUTRI_GGUF"] = str(sorted(ggufs, key=lambda p: p.stat().st_mtime)[-1])

    server = subprocess.Popen(
        ["bash", str(inference / "serve.sh")],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        time.sleep(5)
        result = subprocess.run(
            [sys.executable, str(inference / "test_inference.py"), "--wait-server"],
            env=env,
            check=False,
        )
        if result.returncode != 0:
            return result.returncode
        subprocess.run(
            [sys.executable, str(inference / "benchmark.py")],
            env=env,
            check=False,
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()

    print("\nPASS: Phase 6 GGUF inference pipeline complete", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
