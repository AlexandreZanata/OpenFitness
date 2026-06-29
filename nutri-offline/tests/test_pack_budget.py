"""Unit tests for mobile pack budget rules (BR-MOB-002, N-08-02)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from pack_budget import (  # noqa: E402
    COMPONENT_BUDGETS,
    EMBEDDER_MAX_BYTES,
    PACK_SCHEMA_VERSION,
    PACK_SIZE_LIMIT_BYTES,
    PackBudgetError,
    classify_component,
    validate_component_budget,
    validate_manifest,
    validate_pack_size,
)


class PackBudgetTest(unittest.TestCase):
    def test_pack_size_limit_is_200_mib(self) -> None:
        # GIVEN BR-MOB-002 hard cap
        self.assertEqual(PACK_SIZE_LIMIT_BYTES, 200 * 1024 * 1024)

    def test_validate_pack_size_accepts_under_limit(self) -> None:
        # WHEN size is below 200 MB
        validate_pack_size(PACK_SIZE_LIMIT_BYTES - 1)

    def test_validate_pack_size_rejects_over_limit(self) -> None:
        # WHEN size exceeds 200 MB
        with self.assertRaises(PackBudgetError) as ctx:
            validate_pack_size(PACK_SIZE_LIMIT_BYTES + 1)
        self.assertIn("200", str(ctx.exception))

    def test_classify_component_maps_known_files(self) -> None:
        self.assertEqual(classify_component("vectors.db"), "vector_index")
        self.assertEqual(classify_component("lexicon.db"), "metadata_fts")
        self.assertEqual(classify_component("aliases.db"), "aliases")
        self.assertEqual(classify_component("embedder.onnx"), "embedder")
        self.assertEqual(classify_component("pack.manifest.json"), "manifest")

    def test_validate_component_budget_rejects_oversized_embedder(self) -> None:
        with self.assertRaises(PackBudgetError):
            validate_component_budget("embedder", EMBEDDER_MAX_BYTES + 1)

    def test_validate_manifest_rejects_oversized_pack(self) -> None:
        manifest = {
            "schema_version": 1,
            "pack_id": "nutri-mobile",
            "build_timestamp": "2026-06-28T12:00:00+00:00",
            "size_bytes": PACK_SIZE_LIMIT_BYTES + 1,
            "size_limit_bytes": PACK_SIZE_LIMIT_BYTES,
            "embedder": {
                "model_id": "BAAI/bge-small-en-v1.5",
                "dims": 384,
                "format": "onnx-int8",
                "size_bytes": 1_000_000,
            },
            "index": {
                "record_count": 100,
                "tiers": {"taco": 50, "tbca": 0, "off_tier_c": 50},
                "vector_format": "int8",
            },
            "files": [
                {
                    "path": "embedder.onnx",
                    "size_bytes": 1_000_000,
                    "sha256": "a" * 64,
                }
            ],
        }
        errors = validate_manifest(manifest)
        self.assertTrue(any("size_bytes" in err for err in errors))

    def test_validate_manifest_accepts_valid_sample(self) -> None:
        manifest = {
            "schema_version": 1,
            "pack_id": "nutri-mobile",
            "build_timestamp": "2026-06-28T12:00:00+00:00",
            "size_bytes": 50_000_000,
            "size_limit_bytes": PACK_SIZE_LIMIT_BYTES,
            "embedder": {
                "model_id": "BAAI/bge-small-en-v1.5",
                "dims": 384,
                "format": "onnx-int8",
                "size_bytes": 30_000_000,
            },
            "index": {
                "record_count": 8597,
                "tiers": {"taco": 597, "tbca": 0, "off_tier_c": 8000},
                "vector_format": "int8",
            },
            "files": [
                {
                    "path": "vectors.db",
                    "size_bytes": 20_000_000,
                    "sha256": "b" * 64,
                },
                {
                    "path": "embedder.onnx",
                    "size_bytes": 30_000_000,
                    "sha256": "c" * 64,
                },
            ],
        }
        self.assertEqual(validate_manifest(manifest), [])

    def test_validate_manifest_accepts_v2_semantic_pack(self) -> None:
        manifest = {
            "schema_version": PACK_SCHEMA_VERSION,
            "pack_id": "nutri-mobile",
            "build_timestamp": "2026-06-29T12:00:00+00:00",
            "size_bytes": 50_000_000,
            "size_limit_bytes": PACK_SIZE_LIMIT_BYTES,
            "embedder": {
                "model_id": "BAAI/bge-small-en-v1.5",
                "dims": 384,
                "format": "onnx-int8",
                "size_bytes": 30_000_000,
            },
            "index": {
                "record_count": 8597,
                "surface_count": 28007,
                "tiers": {"taco": 597, "tbca": 0, "off_tier_c": 8000},
                "vector_format": "int8",
                "multi_surface": True,
                "semantic_engine": "v2",
            },
            "files": [
                {
                    "path": "vectors.db",
                    "size_bytes": 20_000_000,
                    "sha256": "b" * 64,
                },
                {
                    "path": "embedder.onnx",
                    "size_bytes": 30_000_000,
                    "sha256": "c" * 64,
                },
            ],
        }
        self.assertEqual(validate_manifest(manifest), [])

    def test_validate_manifest_rejects_v2_without_surfaces(self) -> None:
        manifest = {
            "schema_version": PACK_SCHEMA_VERSION,
            "pack_id": "nutri-mobile",
            "build_timestamp": "2026-06-29T12:00:00+00:00",
            "size_bytes": 50_000_000,
            "size_limit_bytes": PACK_SIZE_LIMIT_BYTES,
            "embedder": {
                "model_id": "BAAI/bge-small-en-v1.5",
                "dims": 384,
                "format": "onnx-int8",
                "size_bytes": 30_000_000,
            },
            "index": {
                "record_count": 8597,
                "surface_count": 100,
                "tiers": {"taco": 597, "tbca": 0, "off_tier_c": 8000},
                "vector_format": "int8",
                "multi_surface": False,
                "semantic_engine": "v1",
            },
            "files": [],
        }
        errors = validate_manifest(manifest)
        self.assertTrue(any("surface_count" in err for err in errors))
        self.assertTrue(any("multi_surface" in err for err in errors))

    def test_component_budgets_sum_leaves_headroom(self) -> None:
        allocated = sum(COMPONENT_BUDGETS.values())
        self.assertLessEqual(allocated, PACK_SIZE_LIMIT_BYTES)


if __name__ == "__main__":
    unittest.main()
