#!/usr/bin/env python3
"""Download USDA FoodData Central bulk Foundation + Branded CSV archives."""

from __future__ import annotations

import sys

from _common import (
    RAW_DIR,
    download_stream,
    extract_zip,
    find_source,
    load_manifest,
    register_download,
    setup_logging,
)

FDC_RELEASE = "2025-04-24"
FDC_PORTAL = "https://fdc.nal.usda.gov/download-datasets/"
DATASETS = {
    "fdc-foundation": (
        f"https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_{FDC_RELEASE}.zip",
        RAW_DIR / "fdc" / f"foundation_food_csv_{FDC_RELEASE}.zip",
        RAW_DIR / "fdc" / f"foundation_food_csv_{FDC_RELEASE}",
    ),
    "fdc-branded": (
        f"https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_branded_food_csv_{FDC_RELEASE}.zip",
        RAW_DIR / "fdc" / f"branded_food_csv_{FDC_RELEASE}.zip",
        RAW_DIR / "fdc" / f"branded_food_csv_{FDC_RELEASE}",
    ),
}
LICENSE = "CC0 1.0 Universal — cite USDA FoodData Central"
ATTRIBUTION = "USDA FoodData Central"


def main() -> int:
    logger = setup_logging("fetch_fdc_bulk")
    manifest = load_manifest()
    for source_id, (url, zip_path, extract_dir) in DATASETS.items():
        entry = find_source(manifest, source_id)
        download_stream(url, zip_path, logger, skip_if_valid=True, manifest_entry=entry)
        register_download(
            source_id=source_id,
            url=url,
            path=zip_path,
            license_text=LICENSE,
            attribution=ATTRIBUTION,
            notes=f"Release {FDC_RELEASE}; portal: {FDC_PORTAL}; extracted to {extract_dir.relative_to(RAW_DIR.parent)}",
            logger=logger,
        )
        extract_zip(zip_path, extract_dir, logger)
    logger.info("FDC bulk download complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
