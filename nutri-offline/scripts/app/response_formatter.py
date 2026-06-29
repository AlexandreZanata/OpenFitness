"""Standardized lookup table renderer (RAG V2 — RAG-V2-03, BR-RET-002)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
sys.path.insert(0, str(DATASET_DIR))

from answers import fmt_g, fmt_kcal, scale_nutrient, source_label  # noqa: E402

from intent_parser import PortionItem  # noqa: E402
from rag_pipeline import RagHit  # noqa: E402


def _scaled(record: dict[str, Any], key: str, portion_g: int) -> float | None:
    basis = record.get("serving_basis") or "100g"
    return scale_nutrient(record.get(key), portion_g, basis=basis)


def _format_portion(portion_g: int) -> str:
    return f"{portion_g}g"


def _format_macro_cell(value: float | None, *, unit: str = "g") -> str:
    if value is None:
        return "—"
    if unit == "kcal":
        return fmt_kcal(value) or "—"
    formatted = fmt_g(value)
    return f"{formatted}{unit}" if formatted else "—"


def format_lookup_table(rows: list[tuple[PortionItem, RagHit | None]]) -> str:
    """Render a grounded markdown nutrition table for one or more items."""
    header = (
        "### Resumo nutricional\n\n"
        "| Alimento | Porção | Fonte | kcal | Proteína | Carboidrato | Gordura |\n"
        "|----------|--------|-------|------|----------|-------------|---------|"
    )
    body_lines: list[str] = []
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    has_totals = False
    sources: set[str] = set()

    for item, hit in rows:
        if hit is None:
            body_lines.append(
                f"| {item.food} | {_format_portion(item.portion_g)} | Não encontrado | — | — | — | — |"
            )
            continue

        record = {
            "source": hit.source,
            "name": hit.name,
            "serving_basis": hit.metadata.get("serving_basis", "100g"),
            "energy_kcal": hit.metadata.get("energy_kcal"),
            "protein_g": hit.metadata.get("protein_g"),
            "carbohydrate_g": hit.metadata.get("carbohydrate_g"),
            "fat_g": hit.metadata.get("fat_g"),
        }
        label = source_label(hit.source)
        sources.add(label)

        kcal = _scaled(record, "energy_kcal", item.portion_g)
        protein = _scaled(record, "protein_g", item.portion_g)
        carbs = _scaled(record, "carbohydrate_g", item.portion_g)
        fat = _scaled(record, "fat_g", item.portion_g)

        for key, value in (
            ("kcal", kcal),
            ("protein", protein),
            ("carbs", carbs),
            ("fat", fat),
        ):
            if value is not None:
                totals[key] += value
                has_totals = True

        body_lines.append(
            "| "
            + " | ".join(
                [
                    hit.name,
                    _format_portion(item.portion_g),
                    label,
                    _format_macro_cell(kcal, unit="kcal"),
                    _format_macro_cell(protein),
                    _format_macro_cell(carbs),
                    _format_macro_cell(fat),
                ]
            )
            + " |"
        )

    if len(rows) > 1 and has_totals:
        body_lines.append(
            "| "
            + " | ".join(
                [
                    "**Total**",
                    "",
                    "",
                    f"**{_format_macro_cell(totals['kcal'], unit='kcal')}**",
                    f"**{_format_macro_cell(totals['protein'])}**",
                    f"**{_format_macro_cell(totals['carbs'])}**",
                    f"**{_format_macro_cell(totals['fat'])}**",
                ]
            )
            + " |"
        )

    footer = ""
    if sources:
        joined = ", ".join(sorted(sources))
        footer = (
            f"\n\n_Fontes: {joined}. Valores calculados a partir dos dados indexados._"
        )

    clarify_notes: list[str] = []
    for _, hit in rows:
        if hit is None:
            continue
        note = hit.metadata.get("ontology_clarify_note")
        if note and note not in clarify_notes:
            clarify_notes.append(str(note))
    if clarify_notes:
        footer += "\n\n" + "\n\n".join(f"_{note}_" for note in clarify_notes)

    return header + "\n" + "\n".join(body_lines) + footer
