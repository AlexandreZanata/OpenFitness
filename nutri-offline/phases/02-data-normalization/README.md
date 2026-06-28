# Phase 2 — Data normalization & unified schema

> **Status:** Done (2026-06-27)  
> **Parent:** [Phase 1](../01-data-acquisition/README.md)  
> **Goal:** Normalize TACO, FDC, OFF (and optional TBCA) into a single schema queryable via DuckDB.

---

## Objective

Transform heterogeneous raw sources into a unified `FoodRecord` schema. Enable cross-source queries, validation against golden rows, and downstream embedding/dataset generation.

---

## Unified schema (`FoodRecord`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | `{source}:{native_id}` |
| `source` | enum | yes | `taco` \| `tbca` \| `fdc` \| `off` |
| `name` | string | yes | Primary display name |
| `name_normalized` | string | yes | Lowercase, accent-stripped for dedup |
| `language` | string | yes | `pt-BR` \| `en` |
| `category` | string | no | Food group / category |
| `energy_kcal` | float | no | Per 100g or per 100ml |
| `protein_g` | float | no | |
| `carbohydrate_g` | float | no | |
| `fat_g` | float | no | |
| `fiber_g` | float | no | |
| `sodium_mg` | float | no | |
| `sugar_g` | float | no | |
| `serving_basis` | string | yes | `100g` \| `100ml` \| `serving` |
| `ingredients_text` | string | no | From OFF primarily |
| `allergens` | string[] | no | Parsed from OFF ingredients |
| `brand` | string | no | OFF / FDC branded |
| `barcode` | string | no | EAN/UPC from OFF |
| `country` | string | no | ISO or tag |
| `source_url` | string | yes | Official citation URL |
| `raw_metadata` | json | no | Source-specific fields preserved |

Output: `data/processed/foods.parquet` (partitioned by source optional).

---

## Target architecture

```
scripts/normalize/
├── schema.py              # FoodRecord dataclass / pydantic model
├── parse_taco.py
├── parse_fdc.py
├── parse_off.py
├── parse_tbca.py          # optional
├── merge.py               # concat + dedup hints
└── validate.py            # golden row checks

data/processed/
├── foods.parquet
├── foods.duckdb           # optional materialized DB
└── stats.json             # row counts, null rates per field
```

---

## Validation rules

| Rule | Check |
|------|-------|
| BR-NORM-001 | TACO golden rows match official values (±1% tolerance for rounding) |
| BR-NORM-002 | `energy_kcal` must be ≥ 0 when present |
| BR-NORM-003 | `source` + `id` unique constraint |
| BR-NORM-004 | OFF Brazil filter: `countries_tags` contains `en:brazil` |

---

## Out of scope

| Item | Phase |
|------|-------|
| Embedding generation | Phase 3 |
| Q&A pair generation | Phase 4 |
| Deduplication across sources (fuzzy merge) | Future — log candidates only in v1 |

---

## Definition of done

- [x] All P0 sources parsed into `FoodRecord`
- [x] `foods.parquet` queryable in DuckDB (2,085,166 rows)
- [x] Golden TACO rows pass validation (±1%)
- [x] `stats.json` documents row counts and field completeness
- [x] Brazil-filtered OFF subset exported (`off-brazil.parquet`, 32,996 rows)

**Gate:** [scripts/validate-nutri-normalization.sh](../../../scripts/validate-nutri-normalization.sh)

---

**References:** [TASKS.md](TASKS.md) · [OFFICIAL-REFERENCE.md](../01-data-acquisition/OFFICIAL-REFERENCE.md)
