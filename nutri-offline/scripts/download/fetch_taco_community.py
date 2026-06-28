#!/usr/bin/env python3
"""Download community TACO CSV backup (derived — NEPA is primary)."""

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

COMMUNITY_FILES = {
    "taco-community-alimentos": (
        "https://raw.githubusercontent.com/machine-learning-mocha/taco/main/formatados/alimentos.csv",
        RAW_DIR / "taco" / "community-alimentos.csv",
    ),
    "taco-community-aminoacidos": (
        "https://raw.githubusercontent.com/machine-learning-mocha/taco/main/formatados/aminoacidos.csv",
        RAW_DIR / "taco" / "community-aminoacidos.csv",
    ),
    "taco-community-acidos-graxos": (
        "https://raw.githubusercontent.com/machine-learning-mocha/taco/main/formatados/acidos-graxos.csv",
        RAW_DIR / "taco" / "community-acidos-graxos.csv",
    ),
}
REPO_URL = "https://github.com/machine-learning-mocha/taco"
LICENSE = "Derived community mirror — cite NEPA/UNICAMP as primary source"
ATTRIBUTION = "Tabela Brasileira de Composição de Alimentos, NEPA/UNICAMP"


def main() -> int:
    logger = setup_logging("fetch_taco_community")
    manifest = load_manifest()
    for source_id, (url, path) in COMMUNITY_FILES.items():
        entry = find_source(manifest, source_id)
        download_stream(url, path, logger, skip_if_valid=True, manifest_entry=entry)
        register_download(
            source_id=source_id,
            url=url,
            path=path,
            license_text=LICENSE,
            attribution=ATTRIBUTION,
            notes=f"Community mirror: {REPO_URL}",
            logger=logger,
        )
    logger.info("TACO community CSV backup complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
