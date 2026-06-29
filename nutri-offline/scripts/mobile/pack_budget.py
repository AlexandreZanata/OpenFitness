"""Mobile pack size budget enforcement (BR-MOB-002, N-08-02)."""

from __future__ import annotations

from dataclasses import dataclass

PACK_SIZE_LIMIT_BYTES = 200 * 1024 * 1024
EMBEDDER_MAX_BYTES = 35 * 1024 * 1024

COMPONENT_BUDGETS: dict[str, int] = {
    "vector_index": 90 * 1024 * 1024,
    "metadata_fts": 45 * 1024 * 1024,
    "aliases": 8 * 1024 * 1024,
    "embedder": EMBEDDER_MAX_BYTES,
    "manifest": 2 * 1024 * 1024,
}

_COMPONENT_BY_FILENAME: dict[str, str] = {
    "vectors.db": "vector_index",
    "lexicon.db": "metadata_fts",
    "synonyms.db": "aliases",
    "aliases.db": "aliases",
    "embedder.onnx": "embedder",
    "pack.manifest.json": "manifest",
}


class PackBudgetError(ValueError):
    """Raised when a mobile pack violates BR-MOB-002 or component allocation."""


@dataclass(frozen=True)
class ComponentUsage:
    component: str
    size_bytes: int
    limit_bytes: int

    @property
    def within_budget(self) -> bool:
        return self.size_bytes <= self.limit_bytes


def classify_component(filename: str) -> str | None:
    """Map a pack file basename to a budget component key."""
    return _COMPONENT_BY_FILENAME.get(filename)


def validate_pack_size(size_bytes: int) -> None:
    """BR-MOB-002: fail when total pack exceeds 200 MB."""
    if size_bytes > PACK_SIZE_LIMIT_BYTES:
        limit_mb = PACK_SIZE_LIMIT_BYTES // (1024 * 1024)
        raise PackBudgetError(
            f"Pack size {size_bytes} bytes exceeds {limit_mb} MB limit ({PACK_SIZE_LIMIT_BYTES} bytes)"
        )


def validate_component_budget(component: str, size_bytes: int) -> None:
    """Fail when a single component exceeds its allocation."""
    limit = COMPONENT_BUDGETS.get(component)
    if limit is None:
        raise PackBudgetError(f"Unknown budget component: {component}")
    if size_bytes > limit:
        limit_mb = limit // (1024 * 1024)
        raise PackBudgetError(
            f"Component '{component}' is {size_bytes} bytes; limit is {limit_mb} MB ({limit} bytes)"
        )


def validate_manifest(manifest: dict) -> list[str]:
    """Return validation errors for a pack.manifest.json payload."""
    errors: list[str] = []

    required_top = (
        "schema_version",
        "pack_id",
        "build_timestamp",
        "size_bytes",
        "size_limit_bytes",
        "embedder",
        "index",
        "files",
    )
    for key in required_top:
        if key not in manifest:
            errors.append(f"Missing required field: {key}")

    size_bytes = manifest.get("size_bytes")
    if isinstance(size_bytes, int):
        if size_bytes > PACK_SIZE_LIMIT_BYTES:
            errors.append(
                f"size_bytes {size_bytes} exceeds limit {PACK_SIZE_LIMIT_BYTES}"
            )

    size_limit = manifest.get("size_limit_bytes")
    if size_limit != PACK_SIZE_LIMIT_BYTES:
        errors.append(
            f"size_limit_bytes must be {PACK_SIZE_LIMIT_BYTES}, got {size_limit!r}"
        )

    embedder = manifest.get("embedder") or {}
    embedder_size = embedder.get("size_bytes")
    if isinstance(embedder_size, int) and embedder_size > EMBEDDER_MAX_BYTES:
        errors.append(
            f"embedder.size_bytes {embedder_size} exceeds {EMBEDDER_MAX_BYTES}"
        )

    files = manifest.get("files") or []
    totals: dict[str, int] = {}
    for entry in files:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path", "")
        size = entry.get("size_bytes")
        if not isinstance(size, int):
            continue
        component = classify_component(str(path).split("/")[-1])
        if component:
            totals[component] = totals.get(component, 0) + size

    for component, used in totals.items():
        limit = COMPONENT_BUDGETS.get(component)
        if limit is not None and used > limit:
            errors.append(
                f"files aggregate for '{component}' is {used} bytes; limit {limit}"
            )

    return errors
