"""Phase 9 semantic engine v2 golden flows (N-09-07)."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from mobile_paths import VECTORS_DB  # noqa: E402
from mobile_assistant import MobileNutriAssistant  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "semantic_v2_golden.jsonl"
TOLERANCE_PCT = 2.0


def within_tolerance(actual: float, expected: float) -> bool:
    if expected == 0:
        return abs(actual) <= 1
    return abs(actual - expected) / abs(expected) * 100 <= TOLERANCE_PCT


def extract_table_kcal(answer: str) -> list[int]:
    rows = [line for line in answer.split("\n") if line.startswith("|") and "kcal" not in line.lower()]
    values: list[int] = []
    for row in rows:
        cells = [cell.strip() for cell in row.split("|") if cell.strip()]
        if len(cells) >= 4 and cells[0] not in {"**Total**", "Alimento"}:
            kcal_cell = cells[3]
            if kcal_cell.replace(".", "").isdigit():
                values.append(int(float(kcal_cell)))
    return values


def extract_portion_g(answer: str) -> int | None:
    match = re.search(r"\|\s*[^|]+\|\s*(\d+)g\s*\|", answer)
    return int(match.group(1)) if match else None


def extract_table_protein(answer: str) -> list[float]:
    rows = [line for line in answer.split("\n") if line.startswith("|") and "prote" not in line.lower()]
    values: list[float] = []
    for row in rows:
        cells = [cell.strip() for cell in row.split("|") if cell.strip()]
        if len(cells) >= 5 and cells[0] not in {"**Total**", "Alimento"}:
            protein_cell = cells[4].lower().replace("g", "").strip()
            try:
                values.append(float(protein_cell.replace(",", ".")))
            except ValueError:
                continue
    return values


@unittest.skipUnless(VECTORS_DB.is_file(), "mobile vectors.db required")
class SemanticV2GoldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assistant = MobileNutriAssistant()

    def test_golden_fixture_rows(self) -> None:
        rows = [
            json.loads(line)
            for line in FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in rows:
            result = self.assistant.ask(row["query"], debug=True)
            self.assertEqual(result.mode, "lookup", row["query"])
            self.assertLess(result.latency_ms, 2000, row["query"])
            self.assertTrue(result.sources, row["query"])

            top = result.sources[0]
            self.assertEqual(top["source"], row["expected_source"], row["query"])
            if row.get("expected_record_id"):
                self.assertEqual(top["id"], row["expected_record_id"], row["query"])
            if row.get("expected_name_contains"):
                self.assertIn(
                    row["expected_name_contains"],
                    top["name"],
                    row["query"],
                )

            if row.get("expected_kcal") is not None:
                kcals = extract_table_kcal(result.answer)
                self.assertTrue(
                    any(within_tolerance(k, row["expected_kcal"]) for k in kcals),
                    f"{row['query']}: expected ~{row['expected_kcal']} kcal, got {kcals}",
                )

            if row.get("expected_portion_g") is not None:
                portion = extract_portion_g(result.answer)
                self.assertEqual(portion, row["expected_portion_g"], row["query"])

            if row.get("expected_protein") is not None:
                proteins = extract_table_protein(result.answer)
                self.assertTrue(
                    any(within_tolerance(p, row["expected_protein"]) for p in proteins),
                    f"{row['query']}: expected ~{row['expected_protein']}g protein, got {proteins}",
                )

            if row.get("expected_clarify_note"):
                self.assertIn("patinho", result.answer.lower(), row["query"])
                self.assertTrue(
                    "default" in result.answer.lower() or "corte" in result.answer.lower(),
                    row["query"],
                )


if __name__ == "__main__":
    unittest.main()
