#!/usr/bin/env python3
"""Phase 1 smoke read — verify raw sources are readable (manual gate N-01-08).

GIVEN Phase 1 downloads completed
WHEN this script runs inside `.local/nutri-offline/venv`
THEN TACO, FDC, and OFF sources pass row-count and schema checks
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "manifest.json"
FDC_RELEASE = "2025-04-24"
LOG_PATH = ROOT / "logs" / "smoke-read-sources.log"


def log(message: str) -> None:
    print(message, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def check_manifest() -> None:
    if not MANIFEST.exists():
        raise SystemExit(f"FAIL: missing manifest at {MANIFEST}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sources = manifest.get("sources", [])
    required = {"taco-official", "fdc-foundation", "fdc-branded", "off-parquet"}
    present = {entry["id"] for entry in sources}
    missing = required - present
    if missing:
        raise SystemExit(f"FAIL: manifest missing sources: {sorted(missing)}")
    for entry in sources:
        path = ROOT / entry["file"]
        if not path.exists() or path.stat().st_size == 0:
            raise SystemExit(f"FAIL: missing or empty file for {entry['id']}: {path}")
        if entry.get("sha256") and entry.get("size_bytes") != path.stat().st_size:
            raise SystemExit(f"FAIL: size mismatch for {entry['id']}")
    log(f"Manifest OK — {len(sources)} sources registered")


def check_taco() -> None:
    import pandas as pd

    path = RAW / "taco" / "taco-oficial.xlsx"
    frames = pd.read_excel(path, sheet_name=None)
    total_rows = sum(len(frame) for frame in frames.values())
    log(f"TACO sheets: {list(frames.keys())}")
    log(f"TACO total rows (all sheets): {total_rows}")
    if total_rows < 400:
        raise SystemExit(f"FAIL: TACO row count too low ({total_rows})")
    log("TACO smoke read PASS")


def check_fdc() -> None:
    import pandas as pd

    foundation_dir = RAW / "fdc" / f"foundation_food_csv_{FDC_RELEASE}"
    food_csv = next(foundation_dir.rglob("food.csv"), None)
    if food_csv is None:
        raise SystemExit(f"FAIL: FDC foundation food.csv not found under {foundation_dir}")
    foods = pd.read_csv(food_csv)
    log(f"FDC Foundation food.csv rows: {len(foods)}")
    if len(foods) < 5000:
        raise SystemExit(f"FAIL: FDC Foundation row count too low ({len(foods)})")

    nutrient_csv = next(foundation_dir.rglob("food_nutrient.csv"), None)
    if nutrient_csv is None:
        raise SystemExit("FAIL: FDC food_nutrient.csv not found")
    nutrients = pd.read_csv(nutrient_csv, nrows=1000)
    log(f"FDC nutrient sample columns: {list(nutrients.columns)[:8]}...")
    log("FDC smoke read PASS")


def check_off() -> None:
    import duckdb

    parquet = RAW / "off" / "food.parquet"
    csv_gz = RAW / "off" / "en.openfoodfacts.org.products.csv.gz"
    connection = duckdb.connect(":memory:")
    if parquet.exists():
        count = connection.execute(
            f"SELECT count(*) FROM read_parquet('{parquet.as_posix()}')"
        ).fetchone()[0]
        columns = connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{parquet.as_posix()}') LIMIT 0"
        ).fetchdf()["column_name"].tolist()
        required = {"product_name", "brands", "countries_tags"}
        missing = required - set(columns)
        if missing:
            raise SystemExit(f"FAIL: OFF parquet missing columns: {sorted(missing)}")
        log(f"OFF parquet rows: {count:,}")
        if count < 1_000_000:
            raise SystemExit(f"FAIL: OFF row count too low ({count})")
    elif csv_gz.exists():
        count = connection.execute(
            f"SELECT count(*) FROM read_csv('{csv_gz.as_posix()}', header=true, delim='\\t')"
        ).fetchone()[0]
        log(f"OFF csv.gz rows: {count:,}")
    else:
        raise SystemExit("FAIL: no OFF parquet or csv.gz found")
    log("OFF smoke read PASS")


def main() -> int:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    log("NutriOffline Phase 1 smoke read")
    check_manifest()
    check_taco()
    check_fdc()
    check_off()
    log("PASS: all Phase 1 smoke read checks succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
