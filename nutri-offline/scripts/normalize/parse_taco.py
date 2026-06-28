#!/usr/bin/env python3
"""Parse TACO 4th edition Excel into FoodRecord rows."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import PROCESSED_DIR, TACO_OFFICIAL_XLSX, TACO_SOURCE_URL
from schema import FoodRecord

SHEET = "CMVCol taco3"
OUTPUT = PROCESSED_DIR / "taco.parquet"

# Official column indices (header rows 0–1; data from row 2)
COL_NUM = 0
COL_NAME = 1
COL_CATEGORY = 0  # category rows use col 0 text, col 1 NaN
COL_KCAL = 3
COL_PROTEIN = 5
COL_FAT = 6
COL_CARB = 8
COL_FIBER = 9
COL_SODIUM = 17


def _to_float(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str):
        cleaned = value.strip().replace(",", ".")
        if cleaned in ("", "NA", "Tr", "tr", "na"):
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def parse_taco_frame(df: pd.DataFrame) -> list[FoodRecord]:
    records: list[FoodRecord] = []
    current_category: str | None = None

    for _, row in df.iterrows():
        food_num = row.iloc[COL_NUM]
        name = row.iloc[COL_NAME]

        if pd.isna(name) and pd.notna(food_num) and isinstance(food_num, str):
            current_category = str(food_num).strip()
            continue

        if pd.isna(name) or pd.isna(food_num):
            continue

        try:
            native_id = str(int(float(food_num)))
        except (TypeError, ValueError):
            continue

        name_str = str(name).strip()
        if not name_str or name_str.lower() == "alimento":
            continue

        records.append(
            FoodRecord.build(
                source="taco",
                native_id=native_id,
                name=name_str,
                language="pt-BR",
                source_url=TACO_SOURCE_URL,
                category=current_category,
                energy_kcal=_to_float(row.iloc[COL_KCAL]),
                protein_g=_to_float(row.iloc[COL_PROTEIN]),
                fat_g=_to_float(row.iloc[COL_FAT]),
                carbohydrate_g=_to_float(row.iloc[COL_CARB]),
                fiber_g=_to_float(row.iloc[COL_FIBER]),
                sodium_mg=_to_float(row.iloc[COL_SODIUM]),
                serving_basis="100g",
                country="BR",
                raw_metadata={"taco_sheet": SHEET, "taco_number": native_id},
            )
        )

    return records


def main() -> int:
    if not TACO_OFFICIAL_XLSX.exists():
        raise SystemExit(f"Missing TACO file: {TACO_OFFICIAL_XLSX}")

    df = pd.read_excel(TACO_OFFICIAL_XLSX, sheet_name=SHEET, header=None)
    records = parse_taco_frame(df)
    if not records:
        raise SystemExit("FAIL: no TACO records parsed")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([record.to_row() for record in records]).to_parquet(OUTPUT, index=False)
    print(f"TACO parsed: {len(records)} rows -> {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
