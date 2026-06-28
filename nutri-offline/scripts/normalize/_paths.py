"""Shared paths for NutriOffline normalization (Phase 2)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_DIR = ROOT / "logs"

FDC_RELEASE = "2025-04-24"
FDC_FOUNDATION_DIR = (
    RAW_DIR
    / "fdc"
    / f"foundation_food_csv_{FDC_RELEASE}"
    / f"FoodData_Central_foundation_food_csv_{FDC_RELEASE}"
)
FDC_BRANDED_DIR = (
    RAW_DIR
    / "fdc"
    / f"branded_food_csv_{FDC_RELEASE}"
    / f"FoodData_Central_branded_food_csv_{FDC_RELEASE}"
)

TACO_OFFICIAL_XLSX = RAW_DIR / "taco" / "taco-oficial.xlsx"
TACO_COMMUNITY_CSV = RAW_DIR / "taco" / "community-alimentos.csv"
OFF_PARQUET = RAW_DIR / "off" / "food.parquet"

TACO_SOURCE_URL = "https://www.nepa.unicamp.br/publicacoes/tabela-taco-excel/"
FDC_SOURCE_URL = "https://fdc.nal.usda.gov/"
OFF_SOURCE_URL = "https://world.openfoodfacts.org/data"

FOODS_PARQUET = PROCESSED_DIR / "foods.parquet"
FOODS_DUCKDB = PROCESSED_DIR / "foods.duckdb"
STATS_JSON = PROCESSED_DIR / "stats.json"
SOURCE_COUNTS_JSON = PROCESSED_DIR / "source_counts.json"

NUTRIENT_IDS = {
    "energy_kcal": 1008,
    "protein_g": 1003,
    "carbohydrate_g": 1005,
    "fat_g": 1004,
    "fiber_g": 1079,
    "sodium_mg": 1093,
    "sugar_g": 1063,
}
