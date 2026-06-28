#!/usr/bin/env python3
"""Select mobile pack record tiers A/B/C from foods.parquet (N-08-03)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import (  # noqa: E402
    DEFAULT_OFF_TIER_C_SIZE,
    FOODS_PARQUET,
    LOG_DIR,
    MOBILE_RECORD_IDS_PARQUET,
)

# BR priority brands aligned with lookup_orchestrator.BRAND_HINTS
PRIORITY_BRANDS = frozenset(
    {
        "vigor",
        "nestle",
        "nestlé",
        "danone",
        "itambé",
        "itambe",
        "qualita",
        "tio joão",
        "tio joao",
        "camil",
        "batavo",
        "piracanjuba",
    }
)

DESKTOP_V1_SOURCES = ("taco", "off")


@dataclass(frozen=True)
class MobileTierSelection:
    tier_a_taco: int
    tier_b_tbca: int
    tier_c_off: int
    excluded_off: int
    desktop_v1_scope: int
    total_selected: int

    def to_dict(self) -> dict:
        return {
            "tiers": {
                "taco": self.tier_a_taco,
                "tbca": self.tier_b_tbca,
                "off_tier_c": self.tier_c_off,
            },
            "excluded_off": self.excluded_off,
            "desktop_v1_scope": self.desktop_v1_scope,
            "total_selected": self.total_selected,
        }


def _normalize_brand(brand: str | None) -> str:
    if not brand:
        return ""
    return brand.strip().lower()


def compute_off_rank_score(row: dict) -> int:
    """Rank OFF products for Tier C inclusion (higher = more likely in pack)."""
    score = 0
    brand = _normalize_brand(row.get("brand"))
    if brand:
        score += 50
        if any(token in brand for token in PRIORITY_BRANDS):
            score += 1000

    name = str(row.get("name") or "").lower()
    if any(token in name for token in PRIORITY_BRANDS):
        score += 500

    if row.get("energy_kcal") is not None:
        score += 100
    if row.get("protein_g") is not None:
        score += 20
    if row.get("carbohydrate_g") is not None:
        score += 20
    if row.get("fat_g") is not None:
        score += 20
    if row.get("barcode"):
        score += 10
    return score


def select_mobile_records(
    *,
    foods_parquet: Path = FOODS_PARQUET,
    output_path: Path = MOBILE_RECORD_IDS_PARQUET,
    off_tier_c_size: int = DEFAULT_OFF_TIER_C_SIZE,
) -> MobileTierSelection:
    """Write mobile_record_ids.parquet with tier labels for index builder."""
    if not foods_parquet.is_file():
        raise FileNotFoundError(f"foods.parquet not found: {foods_parquet}")

    connection = duckdb.connect(":memory:")
    parquet = foods_parquet.as_posix()

    tier_a = connection.execute(
        f"SELECT id, source FROM read_parquet('{parquet}') WHERE source = 'taco'"
    ).fetchall()

    tier_b = connection.execute(
        f"SELECT id, source FROM read_parquet('{parquet}') WHERE source = 'tbca'"
    ).fetchall()

    off_rows = connection.execute(
        f"""
        SELECT id, source, name, brand, energy_kcal, protein_g, carbohydrate_g, fat_g, barcode
        FROM read_parquet('{parquet}')
        WHERE source = 'off'
        """
    ).fetchall()
    off_columns = [
        "id",
        "source",
        "name",
        "brand",
        "energy_kcal",
        "protein_g",
        "carbohydrate_g",
        "fat_g",
        "barcode",
    ]

    ranked_off = sorted(
        off_rows,
        key=lambda row: (
            -compute_off_rank_score(dict(zip(off_columns, row, strict=True))),
            row[0],
        ),
    )
    tier_c = ranked_off[:off_tier_c_size]
    excluded_off = max(0, len(off_rows) - len(tier_c))

    desktop_v1_scope = connection.execute(
        f"""
        SELECT count(*)
        FROM read_parquet('{parquet}')
        WHERE source IN ({", ".join(repr(s) for s in DESKTOP_V1_SOURCES)})
        """
    ).fetchone()[0]

    records: list[tuple[str, str, str]] = []
    for record_id, source in tier_a:
        records.append((record_id, source, "A"))
    for record_id, source in tier_b:
        records.append((record_id, source, "B"))
    for row in tier_c:
        records.append((row[0], row[1], "C"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    connection.execute(
        "CREATE TABLE records (id VARCHAR, source VARCHAR, tier VARCHAR)"
    )
    if records:
        connection.executemany(
            "INSERT INTO records VALUES (?, ?, ?)",
            records,
        )
    connection.execute(
        f"COPY records TO '{output_path.as_posix()}' (FORMAT PARQUET)"
    )

    summary = MobileTierSelection(
        tier_a_taco=len(tier_a),
        tier_b_tbca=len(tier_b),
        tier_c_off=len(tier_c),
        excluded_off=excluded_off,
        desktop_v1_scope=int(desktop_v1_scope),
        total_selected=len(records),
    )

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "mobile-record-selection.json"
    log_path.write_text(
        json.dumps(summary.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Select mobile pack record tiers")
    parser.add_argument(
        "--off-tier-c-size",
        type=int,
        default=DEFAULT_OFF_TIER_C_SIZE,
        help="Max OFF products in Tier C (default: 8000)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=MOBILE_RECORD_IDS_PARQUET,
        help="Output parquet path",
    )
    args = parser.parse_args()

    summary = select_mobile_records(
        output_path=args.output,
        off_tier_c_size=args.off_tier_c_size,
    )
    print(json.dumps(asdict(summary), indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
