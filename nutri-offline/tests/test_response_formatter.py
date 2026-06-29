"""Unit tests for RAG V2 lookup table formatter (RAG-V2-03)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "scripts" / "app"
DATASET_DIR = Path(__file__).resolve().parents[1] / "scripts" / "dataset"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(DATASET_DIR))

from intent_parser import PortionItem  # noqa: E402
from rag_pipeline import RagHit  # noqa: E402
from response_formatter import format_lookup_table  # noqa: E402


def _hit(
    *,
    name: str = "Arroz, tipo 1, cozido",
    source: str = "taco",
    energy: float = 128.26,
    protein: float = 2.52,
    carbs: float = 28.06,
    fat: float = 0.23,
) -> RagHit:
    return RagHit(
        score=0.9,
        id="taco:1",
        name=name,
        source=source,
        rag_context="",
        metadata={
            "energy_kcal": energy,
            "protein_g": protein,
            "carbohydrate_g": carbs,
            "fat_g": fat,
            "serving_basis": "100g",
        },
    )


class ResponseFormatterTest(unittest.TestCase):
    def test_single_item_table_has_macros(self) -> None:
        # GIVEN one matched food at 100g
        rows = [(PortionItem(food="arroz", portion_g=100), _hit())]
        # WHEN formatted
        text = format_lookup_table(rows)
        # THEN table contains grounded TACO values (BR-RET-002)
        self.assertIn("### Resumo nutricional", text)
        self.assertIn("128", text)
        self.assertIn("TACO", text)
        self.assertIn("2.5g", text)

    def test_multi_item_includes_total_row(self) -> None:
        item_a = (PortionItem(food="arroz", portion_g=100), _hit())
        item_b = (
            PortionItem(food="carne", portion_g=200),
            _hit(
                name="Carne bovina, coxão mole, grelhada",
                energy=219.0,
                protein=32.8,
                carbs=0.0,
                fat=9.2,
            ),
        )
        text = format_lookup_table([item_a, item_b])
        self.assertIn("**Total**", text)
        self.assertIn("566", text)

    def test_not_found_item_shown_without_numbers(self) -> None:
        rows = [(PortionItem(food="nutrixyz", portion_g=100), None)]
        text = format_lookup_table(rows)
        self.assertIn("Não encontrado", text)
        not_found_row = [line for line in text.split("\n") if "nutrixyz" in line][0]
        self.assertIn("—", not_found_row)
        self.assertNotRegex(not_found_row, r"\d+\s*kcal")

    def test_ontology_clarify_note_in_footer(self) -> None:
        hit = _hit(name="Carne, bovina, patinho, sem gordura, grelhado")
        hit.metadata["ontology_clarify_note"] = (
            "Nota: 'carne bovina' abrange vários alimentos da categoria."
        )
        text = format_lookup_table([(PortionItem(food="carne bovina", portion_g=100), hit)])
        self.assertIn("Nota: 'carne bovina' abrange vários alimentos da categoria.", text)


if __name__ == "__main__":
    unittest.main()
