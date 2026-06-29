"""Golden substitute flows (Phase 10, BR-SUBST-001)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

MOBILE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "mobile"
sys.path.insert(0, str(MOBILE_DIR))

from mobile_paths import VECTORS_DB  # noqa: E402
from mobile_assistant import MobileNutriAssistant  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "substitute_golden.jsonl"


@unittest.skipUnless(VECTORS_DB.is_file(), "mobile vectors.db required")
class SubstituteGoldenTest(unittest.TestCase):
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
            self.assertEqual(result.mode, row["expected_mode"], row["query"])
            self.assertGreaterEqual(len(result.sources), 2, row["query"])
            substitute = result.sources[1]
            for forbidden in row.get("forbidden_substitute_ids", []):
                self.assertNotEqual(substitute["id"], forbidden, row["query"])
            allowed = row.get("expected_substitute_name_contains_any")
            if allowed:
                name_lower = substitute["name"].lower()
                self.assertTrue(
                    any(token.lower() in name_lower for token in allowed),
                    f"{row['query']}: expected one of {allowed}, got {substitute['name']}",
                )
            elif row.get("expected_substitute_name_contains"):
                self.assertIn(
                    row["expected_substitute_name_contains"].lower(),
                    substitute["name"].lower(),
                    row["query"],
                )


if __name__ == "__main__":
    unittest.main()
