#!/usr/bin/env python3
"""Build nutri-mobile.pack artifact + manifest (N-08-17)."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mobile_paths import (  # noqa: E402
    EMBEDDER_ONNX,
    LEXICON_DB,
    LOG_DIR,
    MOBILE_EMBED_DIM,
    MOBILE_EMBED_MODEL,
    MOBILE_INDEX_DIR,
    PACK_ARTIFACT,
    PACK_MANIFEST,
    VECTORS_DB,
)
from pack_budget import (  # noqa: E402
    PACK_SIZE_LIMIT_BYTES,
    classify_component,
    validate_component_budget,
    validate_manifest,
    validate_pack_size,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    *,
    pack_files: list[Path],
    tier_counts: dict[str, int],
    record_count: int,
    total_size: int,
) -> dict:
    files = []
    embedder_size = 0
    for path in pack_files:
        size = path.stat().st_size
        files.append(
            {
                "path": path.name,
                "size_bytes": size,
                "sha256": sha256_file(path),
            }
        )
        if path.name == "embedder.onnx":
            embedder_size = size

    return {
        "schema_version": 1,
        "pack_id": "nutri-mobile",
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "size_bytes": total_size,
        "size_limit_bytes": PACK_SIZE_LIMIT_BYTES,
        "embedder": {
            "model_id": MOBILE_EMBED_MODEL,
            "dims": MOBILE_EMBED_DIM,
            "format": "onnx-int8",
            "size_bytes": embedder_size,
        },
        "index": {
            "record_count": record_count,
            "tiers": tier_counts,
            "vector_format": "int8",
        },
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build mobile pack artifact")
    parser.add_argument("--output", type=Path, default=PACK_ARTIFACT)
    parser.add_argument("--manifest", type=Path, default=PACK_MANIFEST)
    args = parser.parse_args()

    required = {
        "vectors.db": VECTORS_DB,
        "lexicon.db": LEXICON_DB,
        "embedder.onnx": EMBEDDER_ONNX,
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        print(f"ERROR: missing artifacts: {', '.join(missing)}", file=sys.stderr)
        return 1

    MOBILE_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    staging = MOBILE_INDEX_DIR / "pack-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()

    staged_files: list[Path] = []
    for name, source in required.items():
        target = staging / name
        shutil.copy2(source, target)
        staged_files.append(target)
        component = classify_component(name)
        if component:
            validate_component_budget(component, target.stat().st_size)

    from mobile_sqlite import connect

    connection = connect(str(VECTORS_DB), readonly=True)
    counts = connection.execute(
        """
        SELECT
            sum(CASE WHEN source = 'taco' THEN 1 ELSE 0 END),
            sum(CASE WHEN source = 'tbca' THEN 1 ELSE 0 END),
            sum(CASE WHEN source = 'off' THEN 1 ELSE 0 END),
            count(*)
        FROM food_meta
        """
    ).fetchone()
    connection.close()

    tier_counts = {
        "taco": int(counts[0] or 0),
        "tbca": int(counts[1] or 0),
        "off_tier_c": int(counts[2] or 0),
    }
    record_count = int(counts[3] or 0)

    if args.output.exists():
        args.output.unlink()
    with tarfile.open(args.output, "w:xz") as archive:
        for path in staged_files:
            archive.add(path, arcname=path.name)

    total_size = args.output.stat().st_size
    validate_pack_size(total_size)

    manifest = build_manifest(
        pack_files=staged_files,
        tier_counts=tier_counts,
        record_count=record_count,
        total_size=total_size,
    )
    errors = validate_manifest(manifest)
    if errors:
        print("ERROR: invalid manifest:", errors, file=sys.stderr)
        return 1

    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(staging)

    summary = {
        "pack": str(args.output),
        "manifest": str(args.manifest),
        "size_bytes": total_size,
        "record_count": record_count,
        "tiers": tier_counts,
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "mobile-pack-build.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
