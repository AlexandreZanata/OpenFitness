#!/usr/bin/env python3
"""Phase 11 prerequisites — N-11-00."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RAG_DIR))

from _paths import FOODS_PARQUET, INDEX_DIR, LOG_DIR
from index_catalog import index_snapshot, parquet_snapshot


@dataclass
class PrereqCheck:
    check_id: str
    passed: bool
    detail: str


def run_checks(*, min_disk_gb: float = 15.0) -> list[PrereqCheck]:
    checks: list[PrereqCheck] = []

    parquet_ok = FOODS_PARQUET.is_file()
    checks.append(
        PrereqCheck(
            "N-11-00a",
            parquet_ok,
            str(FOODS_PARQUET) if parquet_ok else "foods.parquet missing",
        )
    )

    if parquet_ok:
        all_snap = parquet_snapshot("all")
        v1_snap = parquet_snapshot("v1")
        stats = {
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "parquet_all_total": all_snap.total_rows,
            "parquet_v1_total": v1_snap.total_rows,
            "source_counts_all": all_snap.source_counts,
            "source_counts_v1": v1_snap.source_counts,
            "index": asdict(index_snapshot()) if index_snapshot() else None,
        }
        stats_path = FOODS_PARQUET.parent / "source_counts.json"
        stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        checks.append(
            PrereqCheck(
                "N-11-00a-stats",
                True,
                f"wrote {stats_path.name} — all={all_snap.total_rows:,} v1={v1_snap.total_rows:,}",
            )
        )
    else:
        checks.append(PrereqCheck("N-11-00a-stats", False, "skipped — no parquet"))

    checks.append(
        PrereqCheck(
            "N-11-00b",
            True,
            "TBCA not in parquet — documented gap; scope=all covers taco/fdc/off only",
        )
    )

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(INDEX_DIR)
    free_gb = usage.free / (1024**3)
    checks.append(
        PrereqCheck(
            "N-11-00c",
            free_gb >= min_disk_gb,
            f"free {free_gb:.1f} GB under {INDEX_DIR} (need ≥{min_disk_gb} GB for scope=all)",
        )
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 11 prerequisite checks")
    parser.add_argument("--min-disk-gb", type=float, default=15.0)
    args = parser.parse_args()

    checks = run_checks(min_disk_gb=args.min_disk_gb)
    passed = all(check.passed for check in checks)
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"{status} {check.check_id}: {check.detail}")

    report = {
        "timestamp": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "passed": passed,
        "checks": [asdict(c) for c in checks],
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "full-catalog-prereqs.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\n{'PASS' if passed else 'FAIL'}: Phase 11 prerequisites")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
