"""Shared helpers for NutriOffline data acquisition (Phase 1)."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "manifest.json"
LOG_DIR = ROOT / "logs"

CHUNK_SIZE = 1024 * 1024
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


@dataclass
class SourceRecord:
    id: str
    url: str
    file: str
    downloaded_at: str
    sha256: str
    size_bytes: int
    license: str
    attribution: str
    notes: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def setup_logging(name: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"download-{datetime.now().strftime('%Y-%m-%d')}.log"
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"version": 1, "sources": []}
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def find_source(manifest: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    for entry in manifest.get("sources", []):
        if entry.get("id") == source_id:
            return entry
    return None


def upsert_source(record: SourceRecord) -> None:
    manifest = load_manifest()
    sources = [entry for entry in manifest.get("sources", []) if entry.get("id") != record.id]
    sources.append(asdict(record))
    manifest["sources"] = sorted(sources, key=lambda item: item["id"])
    save_manifest(manifest)


def file_matches_manifest(path: Path, manifest_entry: dict[str, Any] | None) -> bool:
    if manifest_entry is None or not path.exists() or path.stat().st_size == 0:
        return False
    if manifest_entry.get("size_bytes") != path.stat().st_size:
        return False
    expected = manifest_entry.get("sha256")
    if not expected:
        return False
    return sha256_file(path) == expected


def download_stream(
    url: str,
    destination: Path,
    logger: logging.Logger,
    *,
    skip_if_valid: bool = False,
    manifest_entry: dict[str, Any] | None = None,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if skip_if_valid and file_matches_manifest(destination, manifest_entry):
        logger.info("Skipping %s — checksum matches manifest", destination.name)
        return destination

    temp_path = destination.with_suffix(destination.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Downloading %s (attempt %s/%s)", url, attempt, MAX_RETRIES)
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "NutriOffline/1.0 (local research; OpenFitness)"},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                last_report = time.monotonic()
                with temp_path.open("wb") as handle:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        now = time.monotonic()
                        if total and now - last_report >= 10:
                            pct = downloaded * 100 / total
                            logger.info(
                                "Progress %s: %.1f%% (%s / %s bytes)",
                                destination.name,
                                pct,
                                downloaded,
                                total,
                            )
                            last_report = now
            temp_path.replace(destination)
            logger.info("Saved %s (%s bytes)", destination, destination.stat().st_size)
            return destination
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            logger.warning("Download failed: %s", error)
            if temp_path.exists():
                temp_path.unlink()
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
    raise RuntimeError(f"Failed to download {url}") from last_error


def extract_zip(zip_path: Path, destination_dir: Path, logger: logging.Logger) -> Path:
    import zipfile

    destination_dir.mkdir(parents=True, exist_ok=True)
    marker = destination_dir / ".extracted"
    if marker.exists():
        logger.info("Skipping extract — marker present for %s", zip_path.name)
        return destination_dir
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(destination_dir)
    marker.write_text(f"extracted_from={zip_path.name}\n", encoding="utf-8")
    logger.info("Extracted %s -> %s", zip_path.name, destination_dir)
    return destination_dir


def register_download(
    *,
    source_id: str,
    url: str,
    path: Path,
    license_text: str,
    attribution: str,
    notes: str = "",
    logger: logging.Logger,
) -> SourceRecord:
    record = SourceRecord(
        id=source_id,
        url=url,
        file=str(path.relative_to(ROOT)),
        downloaded_at=utc_now_iso(),
        sha256=sha256_file(path),
        size_bytes=path.stat().st_size,
        license=license_text,
        attribution=attribution,
        notes=notes,
    )
    upsert_source(record)
    logger.info("Manifest updated for %s", source_id)
    return record
