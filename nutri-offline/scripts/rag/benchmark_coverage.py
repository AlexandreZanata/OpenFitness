#!/usr/bin/env python3
"""G-COV coverage gate — Phase 11 (N-11-10)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import LOG_DIR
from index_catalog import (
    fetch_index_row,
    index_snapshot,
    load_index_metadata,
    parquet_snapshot,
    sample_parquet_ids,
)

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "full_catalog_coverage_seed.json"


@dataclass
class CoverageCheck:
    check_id: str
    passed: bool
    detail: str


def _load_seed() -> dict:
    if FIXTURE.is_file():
        return json.loads(FIXTURE.read_text(encoding="utf-8"))
    return {"round_trip_sample_size": 200, "round_trip_seed": 110629}


def run_coverage_checks(*, scope: str, require_scope: str | None = None) -> list[CoverageCheck]:
    checks: list[CoverageCheck] = []
    seed_cfg = _load_seed()
    parquet = parquet_snapshot(scope)
    index = index_snapshot()

    if index is None:
        checks.append(CoverageCheck("G-COV-00", False, "metadata.json missing"))
        return checks

    if require_scope and index.scope != require_scope:
        checks.append(
            CoverageCheck(
                "G-COV-SCOPE",
                False,
                f"index scope={index.scope!r}, required {require_scope!r}",
            )
        )

    row_parity = index.record_count == parquet.total_rows
    checks.append(
        CoverageCheck(
            "G-COV-01",
            row_parity,
            f"index={index.record_count:,} parquet({scope})={parquet.total_rows:,}",
        )
    )

    source_ok = index.source_counts == parquet.source_counts
    if not index.source_counts and row_parity:
        source_ok = True
        source_detail = f"legacy metadata (no source_counts) — rebuild index for N-11-03"
    else:
        source_detail = f"index={index.source_counts} parquet={parquet.source_counts}"
    checks.append(
        CoverageCheck(
            "G-COV-02",
            source_ok,
            source_detail,
        )
    )

    sample_size = int(seed_cfg.get("round_trip_sample_size", 200))
    sample_seed = int(seed_cfg.get("round_trip_seed", 110629))
    sample_ids = sample_parquet_ids(scope, count=sample_size, seed=sample_seed)
    mismatches = 0
    missing = 0
    for record_id in sample_ids:
        row = fetch_index_row(record_id)
        if row is None:
            missing += 1
            continue
        parquet_row = _parquet_energy(record_id)
        index_kcal = row.get("energy_kcal")
        if parquet_row is not None and index_kcal is not None:
            if abs(float(parquet_row) - float(index_kcal)) > 0.01:
                mismatches += 1
    round_trip_ok = missing == 0 and mismatches == 0
    checks.append(
        CoverageCheck(
            "G-COV-03",
            round_trip_ok,
            f"sample={len(sample_ids)} missing={missing} kcal_mismatch={mismatches}",
        )
    )

    empty_names = 0
    for record_id in sample_ids[: min(50, len(sample_ids))]:
        row = fetch_index_row(record_id)
        if row is not None and not str(row.get("name", "")).strip():
            empty_names += 1
    checks.append(
        CoverageCheck(
            "G-COV-04",
            empty_names == 0,
            f"empty_names_in_sample={empty_names}",
        )
    )
    return checks


def _parquet_energy(record_id: str) -> float | None:
    import duckdb

    from _paths import FOODS_PARQUET

    connection = duckdb.connect(":memory:")
    row = connection.execute(
        f"""
        SELECT energy_kcal
        FROM read_parquet('{FOODS_PARQUET.as_posix()}')
        WHERE id = ?
        LIMIT 1
        """,
        [record_id],
    ).fetchone()
    if row is None:
        return None
    return None if row[0] is None else float(row[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Full catalog coverage gate (G-COV)")
    parser.add_argument("--scope", choices=["v1", "all"], default="all")
    parser.add_argument("--require-scope", choices=["v1", "all"], default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    meta = load_index_metadata()
    effective_scope = str(meta.get("scope", args.scope))
    checks = run_coverage_checks(scope=effective_scope, require_scope=args.require_scope)
    passed = all(check.passed for check in checks)

    report = {
        "timestamp": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "index_scope": effective_scope,
        "require_scope": args.require_scope,
        "passed": passed,
        "checks": [asdict(check) for check in checks],
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for check in checks:
            status = "PASS" if check.passed else "FAIL"
            print(f"{status} {check.check_id}: {check.detail}")
        print(f"\n{'PASS' if passed else 'FAIL'}: G-COV coverage gate")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not passed and args.require_scope and effective_scope != args.require_scope:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        print(
            f"\nNext: build full index — "
            f"python scripts/rag/build_index_v2.py --scope all --device cuda",
            file=sys.stderr,
        )

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
