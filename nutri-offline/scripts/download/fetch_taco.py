#!/usr/bin/env python3
"""Download official TACO 4th edition Excel (NEPA/UNICAMP)."""

from __future__ import annotations

import sys
from pathlib import Path

from _common import (
    RAW_DIR,
    download_stream,
    find_source,
    load_manifest,
    register_download,
    setup_logging,
)

TACO_PAGE_URL = "https://nepa.unicamp.br/publicacoes/tabela-taco-excel/"
TACO_FILE_URL = (
    "https://nepa.unicamp.br/wp-content/uploads/sites/27/2023/10/Taco-4a-Edicao.xlsx"
)
OUTPUT = RAW_DIR / "taco" / "taco-oficial.xlsx"
LICENSE = "Public academic research data — cite NEPA/UNICAMP"
ATTRIBUTION = "Tabela Brasileira de Composição de Alimentos, NEPA/UNICAMP"


def main() -> int:
    logger = setup_logging("fetch_taco")
    manifest = load_manifest()
    entry = find_source(manifest, "taco-official")
    download_stream(
        TACO_FILE_URL,
        OUTPUT,
        logger,
        skip_if_valid=True,
        manifest_entry=entry,
    )
    register_download(
        source_id="taco-official",
        url=TACO_FILE_URL,
        path=OUTPUT,
        license_text=LICENSE,
        attribution=ATTRIBUTION,
        notes=f"Landing page: {TACO_PAGE_URL}",
        logger=logger,
    )
    logger.info("TACO official download complete: %s", OUTPUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
