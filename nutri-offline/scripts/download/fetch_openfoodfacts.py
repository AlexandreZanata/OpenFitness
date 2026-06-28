#!/usr/bin/env python3
"""Download Open Food Facts simplified Parquet export (Hugging Face)."""

from __future__ import annotations

import sys

from _common import (
    RAW_DIR,
    download_stream,
    find_source,
    load_manifest,
    register_download,
    setup_logging,
)

OFF_PORTAL = "https://world.openfoodfacts.org/data"
OFF_PARQUET_URL = (
    "https://huggingface.co/datasets/openfoodfacts/product-database/"
    "resolve/main/food.parquet?download=true"
)
OFF_CSV_FALLBACK = (
    "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
)
OUTPUT = RAW_DIR / "off" / "food.parquet"
LICENSE = "Open Database License (ODbL) — attribution required"
ATTRIBUTION = "Open Food Facts contributors"


def main() -> int:
    logger = setup_logging("fetch_openfoodfacts")
    manifest = load_manifest()
    entry = find_source(manifest, "off-parquet")
    try:
        download_stream(
            OFF_PARQUET_URL,
            OUTPUT,
            logger,
            skip_if_valid=True,
            manifest_entry=entry,
        )
        register_download(
            source_id="off-parquet",
            url=OFF_PARQUET_URL,
            path=OUTPUT,
            license_text=LICENSE,
            attribution=ATTRIBUTION,
            notes=f"Parquet export; portal: {OFF_PORTAL}; Brazil filter deferred to Phase 2",
            logger=logger,
        )
    except RuntimeError as error:
        logger.error("Parquet download failed: %s", error)
        logger.info("Fallback: CSV.gz from official static host")
        csv_gz = RAW_DIR / "off" / "en.openfoodfacts.org.products.csv.gz"
        entry = find_source(manifest, "off-csv-gz")
        download_stream(
            OFF_CSV_FALLBACK,
            csv_gz,
            logger,
            skip_if_valid=True,
            manifest_entry=entry,
        )
        register_download(
            source_id="off-csv-gz",
            url=OFF_CSV_FALLBACK,
            path=csv_gz,
            license_text=LICENSE,
            attribution=ATTRIBUTION,
            notes=f"CSV.gz fallback; portal: {OFF_PORTAL}",
            logger=logger,
        )
    logger.info("Open Food Facts download complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
