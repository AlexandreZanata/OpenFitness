#!/usr/bin/env python3
"""Explore TBCA (USP) export options — Phase 1 P1 complement."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from _common import RAW_DIR, setup_logging, utc_now_iso

TBCA_PORTAL = "https://www.tbca.net.br/"
OUTPUT_DIR = RAW_DIR / "tbca"
FINDINGS_PATH = OUTPUT_DIR / "access-notes.json"


def probe_url(url: str) -> dict[str, str | int]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NutriOffline/1.0 (local research)"},
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return {
                "url": url,
                "status": str(response.status),
                "content_type": response.headers.get("Content-Type", ""),
            }
    except urllib.error.HTTPError as error:
        return {"url": url, "status": str(error.code), "content_type": ""}
    except urllib.error.URLError as error:
        return {"url": url, "status": "error", "content_type": str(error.reason)}


def main() -> int:
    logger = setup_logging("fetch_tbca")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    findings = {
        "explored_at": utc_now_iso(),
        "portal": TBCA_PORTAL,
        "decision": "defer_full_ingest_v1",
        "rationale": (
            "TBCA portal is web-only search with no documented bulk export or public API. "
            "Manual per-food lookup only. Full automation blocked for Phase 1 — "
            "TACO + FDC + OFF sufficient for v1 per IMPLEMENTATION-PLAN."
        ),
        "priority": "P1 complement for Phase 2+ if manual export or API becomes available",
        "probes": [
            probe_url(TBCA_PORTAL),
            probe_url("https://www.tbca.net.br/base/tabela/lista"),
        ],
        "next_steps": [
            "Revisit TBCA when normalization needs biodiversity foods missing from TACO",
            "Contact USP/TBCA for bulk academic access if required",
        ],
    }
    FINDINGS_PATH.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logger.info("TBCA exploration notes saved to %s", FINDINGS_PATH)
    logger.info("Decision: defer full TBCA ingest — documented for Phase 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
