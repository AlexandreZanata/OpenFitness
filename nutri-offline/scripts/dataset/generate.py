#!/usr/bin/env python3
"""Generate ChatML fine-tuning dataset from normalized foods (Phase 4)."""

from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from answers import (
    generate_allergen,
    generate_comparison,
    generate_direct_lookup,
    generate_household_portion,
    generate_portion_math,
    generate_reasoning,
    generate_substitution,
    generate_unknown_refusal,
    source_label,
)
from constants import STRATEGY_WEIGHTS, SYSTEM_PROMPT, TARGET_TOTAL
from grounding import validate_example
from records import (
    connect,
    fetch_comparison_pairs,
    fetch_fdc_foundation,
    fetch_off_brazil,
    fetch_off_with_ingredients,
    fetch_records_by_ids,
    fetch_substitution_pairs,
    fetch_taco,
)
from unknown_foods import UNKNOWN_FOOD_NAMES
from templates import QuestionTemplate, templates_for_category

PORTION_GRAMS = [30, 50, 80, 100, 120, 150, 200, 250]

ALLERGEN_KEYWORDS: dict[str, list[str]] = {
    "glúten": ["gluten", "glúten", "trigo", "centeio", "cevada"],
    "lactose": ["lactose", "leite", "lácteo", "lacteo"],
    "soja": ["soja", "soy"],
    "amendoim": ["amendoim", "peanut"],
    "ovo": ["ovo", "egg"],
}


def build_example(
    *,
    user_content: str,
    assistant_content: str,
    template: QuestionTemplate,
    grounding: dict[str, Any],
    language: str,
) -> dict[str, Any]:
    example_id = str(uuid.uuid4())
    chatml = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
    }
    log_entry = {
        "example_id": example_id,
        "template_id": template.template_id,
        "category": template.category,
        "language": language,
        "grounding": grounding,
    }
    return {"example_id": example_id, **chatml, "generation_log": log_entry}


def ingredient_contains(ingredients: str | None, keywords: list[str]) -> bool:
    if not ingredients:
        return False
    text = ingredients.lower()
    return any(keyword in text for keyword in keywords)


def generate_direct_examples(
    records: list[dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates_pt = templates_for_category("direct_lookup", "pt")
    templates_en = templates_for_category("direct_lookup", "en")
    index = 0
    while len(examples) < count and records:
        record = records[index % len(records)]
        index += 1
        use_en = rng.random() < 0.05
        template = rng.choice(templates_en if use_en else templates_pt)
        language = template.language
        label = source_label(record["source"])
        question = template.format_question(food_name=record["name"], source=label)
        answer, grounding = generate_direct_lookup(record, language)
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language=language,
        )
        if not validate_example(example):
            examples.append(example)
    return examples


def generate_portion_examples(
    records: list[dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates_pt = templates_for_category("portion_math", "pt")
    templates_en = templates_for_category("portion_math", "en")
    index = 0
    while len(examples) < count and records:
        record = records[index % len(records)]
        index += 1
        portion_g = rng.choice(PORTION_GRAMS)
        use_en = rng.random() < 0.05
        template = rng.choice(templates_en if use_en else templates_pt)
        language = template.language
        label = source_label(record["source"])
        question = template.format_question(
            food_name=record["name"],
            portion_g=portion_g,
            source=label,
        )
        answer, grounding = generate_portion_math(record, portion_g, language)
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language=language,
        )
        if not validate_example(example):
            examples.append(example)
    return examples


NUTRIENT_LABELS = {
    "protein_g": "proteína",
    "carbohydrate_g": "carboidratos",
    "fat_g": "gordura",
    "energy_kcal": "calorias",
}


def generate_comparison_examples(
    pairs: list[tuple[dict[str, Any], dict[str, Any], str]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates_pt = templates_for_category("comparison", "pt")
    templates_en = templates_for_category("comparison", "en")
    for index in range(count):
        if not pairs:
            break
        record_a, record_b, nutrient_key = pairs[index % len(pairs)]
        use_en = rng.random() < 0.05
        template = rng.choice(templates_en if use_en else templates_pt)
        language = template.language
        label = source_label(record_a["source"])
        nutrient_label = NUTRIENT_LABELS.get(nutrient_key, nutrient_key)
        question = template.format_question(
            food_a=record_a["name"],
            food_b=record_b["name"],
            nutrient=nutrient_label,
            source=label,
        )
        try:
            answer, grounding = generate_comparison(
                record_a, record_b, nutrient_key, nutrient_label, language
            )
        except ValueError:
            continue
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language=language,
        )
        if not validate_example(example):
            examples.append(example)
    return examples


def generate_substitution_examples(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates = templates_for_category("substitution", "pt")
    for index in range(count):
        if not pairs:
            break
        record, alt = pairs[index % len(pairs)]
        template = rng.choice(templates)
        label = source_label(record["source"])
        question = template.format_question(
            food_name=record["name"],
            alt_name=alt["name"],
            source=label,
        )
        try:
            answer, grounding = generate_substitution(record, alt, "pt")
        except ValueError:
            continue
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language="pt",
        )
        if not validate_example(example):
            examples.append(example)
    return examples


def generate_allergen_examples(
    records: list[dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates = templates_for_category("allergen", "pt")
    index = 0
    while len(examples) < count and records:
        record = records[index % len(records)]
        index += 1
        allergen = rng.choice(list(ALLERGEN_KEYWORDS.keys()))
        keywords = ALLERGEN_KEYWORDS[allergen]
        contains = ingredient_contains(record.get("ingredients_text"), keywords)
        template = rng.choice(templates)
        label = source_label(record["source"])
        question = template.format_question(
            food_name=record["name"],
            allergen=allergen,
            source=label,
        )
        answer, grounding = generate_allergen(record, allergen, contains)
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language="pt",
        )
        if not validate_example(example):
            examples.append(example)
    return examples


def generate_reasoning_examples(
    records: list[dict[str, Any]],
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates_pt = templates_for_category("reasoning", "pt")
    templates_en = templates_for_category("reasoning", "en")
    index = 0
    while len(examples) < count and records:
        record = records[index % len(records)]
        index += 1
        if record.get("energy_kcal") is None:
            continue
        use_en = rng.random() < 0.05
        template = rng.choice(templates_en if use_en else templates_pt)
        language = template.language
        label = source_label(record["source"])
        question = template.format_question(food_name=record["name"], source=label)
        answer, grounding = generate_reasoning(record, language)
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language=language,
        )
        if not validate_example(example):
            examples.append(example)
    return examples


def generate_unknown_refusal_examples(count: int, rng: random.Random) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates_pt = templates_for_category("unknown_refusal", "pt")
    templates_en = templates_for_category("unknown_refusal", "en")
    foods = list(UNKNOWN_FOOD_NAMES)
    rng.shuffle(foods)
    index = 0
    while len(examples) < count and foods:
        food_name = foods[index % len(foods)]
        index += 1
        use_en = rng.random() < 0.05
        template = rng.choice(templates_en if use_en else templates_pt)
        language = template.language
        question = template.format_question(food_name=food_name)
        answer, grounding = generate_unknown_refusal(food_name, language)
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language=language,
        )
        if not validate_example(example):
            examples.append(example)
    return examples


def load_household_entries() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "config" / "semantic" / "household_portions.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("entries", []))


def generate_household_portion_examples(
    connection,
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    templates = templates_for_category("household_portion", "pt")
    entries = load_household_entries()
    record_ids = [entry["default_record_id"] for entry in entries if entry.get("default_record_id")]
    by_id = fetch_records_by_ids(connection, record_ids)
    slots: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for entry in entries:
        record = by_id.get(entry.get("default_record_id", ""))
        if not record:
            continue
        for unit in entry.get("units", []):
            slots.append((entry, unit))
    rng.shuffle(slots)
    index = 0
    while len(examples) < count and slots:
        entry, unit = slots[index % len(slots)]
        index += 1
        record = by_id.get(entry["default_record_id"])
        if not record:
            continue
        unit_label = str(unit.get("unit", "unidade"))
        if unit_label == "un":
            unit_label = "uma unidade"
        elif unit_label == "unidade":
            unit_label = "uma unidade"
        elif unit_label == "media":
            unit_label = "uma média"
        elif unit_label == "inteira":
            unit_label = "uma inteira"
        else:
            unit_label = f"uma {unit_label}"
        portion_g = int(unit["grams"])
        template = rng.choice(templates)
        food_display = entry.get("food", record["name"])
        label = source_label(record["source"])
        question = template.format_question(
            food_name=food_display,
            unit_label=unit_label,
            source=label,
        )
        answer, grounding = generate_household_portion(
            record,
            portion_g=portion_g,
            unit_label=unit_label,
            template_language="pt",
        )
        example = build_example(
            user_content=question,
            assistant_content=answer,
            template=template,
            grounding=grounding,
            language="pt",
        )
        if not validate_example(example):
            examples.append(example)
    return examples


def strategy_counts(total: int) -> dict[str, int]:
    counts = {name: int(total * weight) for name, weight in STRATEGY_WEIGHTS.items()}
    delta = total - sum(counts.values())
    counts["direct_lookup"] += delta
    return counts


def generate_dataset(*, target: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    counts = strategy_counts(target)
    connection = connect()

    taco = fetch_taco(connection)
    fdc = fetch_fdc_foundation(connection, limit=1000)
    off = fetch_off_brazil(connection, limit=2000)
    off_ingredients = fetch_off_with_ingredients(connection, limit=1000)

    # Oversample TACO: repeat records for direct/portion/reasoning
    taco_pool = taco * 8
    mixed_pool = taco * 4 + fdc + off
    rng.shuffle(mixed_pool)
    rng.shuffle(taco_pool)

    comparison_taco = fetch_comparison_pairs(connection, "taco", limit=200)
    comparison_off = fetch_comparison_pairs(connection, "off", limit=200)
    comparison_pairs = comparison_taco + comparison_off

    subst_taco = fetch_substitution_pairs(connection, "taco", limit=150)
    subst_off = fetch_substitution_pairs(connection, "off", limit=150)
    subst_pairs = subst_taco + subst_off

    examples: list[dict[str, Any]] = []
    examples.extend(generate_direct_examples(taco_pool + mixed_pool, counts["direct_lookup"], rng))
    examples.extend(generate_portion_examples(taco_pool + mixed_pool, counts["portion_math"], rng))
    examples.extend(generate_comparison_examples(comparison_pairs, counts["comparison"], rng))
    examples.extend(generate_substitution_examples(subst_pairs, counts["substitution"], rng))
    examples.extend(generate_allergen_examples(off_ingredients, counts["allergen"], rng))
    examples.extend(generate_reasoning_examples(taco_pool + mixed_pool, counts["reasoning"], rng))
    examples.extend(generate_unknown_refusal_examples(counts["unknown_refusal"], rng))
    examples.extend(generate_household_portion_examples(connection, counts["household_portion"], rng))

    rng.shuffle(examples)
    return examples[:target]


def write_jsonl(path: Path, examples: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False) + "\n")


def main() -> int:
    from _paths import DATASETS_DIR, GENERATION_LOG, RAW_GENERATED

    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=TARGET_TOTAL)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    examples = generate_dataset(target=args.target, seed=args.seed)
    write_jsonl(RAW_GENERATED, examples)

    with GENERATION_LOG.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example["generation_log"], ensure_ascii=False) + "\n")

    print(f"Generated {len(examples)} examples -> {RAW_GENERATED}", flush=True)
    print(f"Generation log -> {GENERATION_LOG}", flush=True)
    print(f"Output dir: {DATASETS_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
