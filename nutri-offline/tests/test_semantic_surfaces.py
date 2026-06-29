"""Unit tests for multi-surface generation (N-09-04, BR-SURF-001)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from semantic_surfaces import (  # noqa: E402
    BR_SURF_001_TIER_CAPS,
    INTENT_PROTOTYPES,
    estimate_int8_vector_bytes,
    generate_surfaces_for_record,
    load_intent_prototypes,
    surface_kinds,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "semantic_surfaces.jsonl"
INTENT_JSON = Path(__file__).resolve().parents[1] / "config" / "semantic" / "intent_prototypes.json"


class SemanticSurfaceGenerationTest(unittest.TestCase):
    def test_golden_fixture_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            surfaces = generate_surfaces_for_record(
                record_id=row["record_id"],
                name=row["name"],
                name_normalized=row["name_normalized"],
                category=row.get("category", ""),
                source=row["source"],
                brand=row.get("brand", ""),
                tier=row["tier"],
                aliases=row.get("aliases", []),
            )
            kinds = surface_kinds(surfaces)
            for expected_kind in row["expected_kinds"]:
                self.assertIn(expected_kind, kinds, row["record_id"])
            self.assertGreaterEqual(len(surfaces), row["expected_min_surfaces"], row["record_id"])
            self.assertLessEqual(len(surfaces), row["expected_max_surfaces"], row["record_id"])
            cap = BR_SURF_001_TIER_CAPS[row["tier"]]
            self.assertLessEqual(len(surfaces), cap, row["record_id"])

    def test_surface_ids_are_unique_per_record(self) -> None:
        surfaces = generate_surfaces_for_record(
            record_id="taco:3",
            name="Arroz, tipo 1, cozido",
            name_normalized="arroz tipo 1 cozido",
            category="Cereais e derivados",
            source="taco",
            brand="",
            tier="A",
            aliases=["arroz", "arroz cozido"],
        )
        ids = [surface.surface_id for surface in surfaces]
        self.assertEqual(len(ids), len(set(ids)))

    def test_taco_surfaces_include_faq_for_arroz(self) -> None:
        surfaces = generate_surfaces_for_record(
            record_id="taco:3",
            name="Arroz, tipo 1, cozido",
            name_normalized="arroz tipo 1 cozido",
            category="Cereais e derivados",
            source="taco",
            brand="",
            tier="A",
            aliases=["arroz cozido"],
        )
        faq_texts = [surface.search_text for surface in surfaces if surface.surface_kind == "faq"]
        self.assertTrue(any("calorias" in text for text in faq_texts))
        self.assertTrue(any("arroz" in text for text in faq_texts))


class SemanticSurfaceBudgetTest(unittest.TestCase):
    def test_taco_597_estimate_within_vector_budget(self) -> None:
        # GIVEN ~597 TACO records at tier A cap 40 surfaces each
        estimated = estimate_int8_vector_bytes(597 * BR_SURF_001_TIER_CAPS["A"])
        # THEN int8 payload stays well under 90 MB vector_index budget
        self.assertLess(estimated, 90 * 1024 * 1024)


class IntentPrototypeTest(unittest.TestCase):
    def test_load_intent_prototypes_json(self) -> None:
        prototypes = load_intent_prototypes(INTENT_JSON)
        self.assertGreaterEqual(len(prototypes), 5)
        self.assertEqual(prototypes[0]["id"], "intent_calories")

    def test_builtin_intent_prototypes_match_json(self) -> None:
        loaded = load_intent_prototypes(INTENT_JSON)
        self.assertEqual(len(INTENT_PROTOTYPES), len(loaded))


class SemanticSurfaceIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vectors_db = Path(__file__).resolve().parents[1] / "indexes" / "nutri-mobile" / "vectors.db"
        if not vectors_db.is_file():
            raise unittest.SkipTest("vectors.db not built")
        from mobile_sqlite import connect  # noqa: E402

        connection = connect(str(vectors_db), readonly=True)
        cls.surface_count = connection.execute(
            "SELECT COUNT(*) FROM food_surfaces"
        ).fetchone()[0]
        connection.close()

    def test_vectors_db_contains_multi_surface_table(self) -> None:
        self.assertGreater(self.surface_count, 5000)


if __name__ == "__main__":
    unittest.main()
