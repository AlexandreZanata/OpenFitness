# Phase 2 tasks — Data normalization

> **ID:** N-02 · Unified schema  
> **Quality gate:** Golden TACO rows pass; DuckDB queries return expected counts  
> **Status:** Done (2026-06-27)  
> **Depends on:** [Phase 1](../01-data-acquisition/TASKS.md)

---

## Owner decisions (resolve before N-02-01)

| Decision | Options | Status |
|----------|---------|--------|
| **Output format** | Parquet (recommended) · DuckDB native table | ✅ Parquet + DuckDB |
| **OFF Brazil filter** | At parse time (recommended) · view at query time | ✅ At parse time |
| **Missing nutrients** | null · 0 · omit field | ✅ null |
| **TBCA parser** | Include if Phase 1 downloaded · skip | ✅ Skipped (deferred Phase 1) |
| **Unit normalization** | All per 100g/100ml (recommended) | ✅ per 100g/100ml |

---

## 0. Prerequisites

- [x] Phase 1 complete — raw files + manifest
- [x] Read [README.md](README.md) schema
- [x] Read [OFFICIAL-REFERENCE.md](../01-data-acquisition/OFFICIAL-REFERENCE.md)
- [x] Golden validation rows documented

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-02-01 | Define FoodRecord schema | `scripts/normalize/schema.py` | P0 | ✅ |
| N-02-02 | Parse TACO Excel/CSV | `scripts/normalize/parse_taco.py` | P0 | ✅ |
| N-02-03 | Parse FDC bulk | `scripts/normalize/parse_fdc.py` | P0 | ✅ |
| N-02-04 | Parse OFF Parquet | `scripts/normalize/parse_off.py` | P0 | ✅ |
| N-02-05 | Merge + write Parquet | `scripts/normalize/merge.py` | P0 | ✅ |
| N-02-06 | Validation + golden tests | `scripts/normalize/validate.py` | P0 | ✅ |
| N-02-07 | DuckDB materialized DB | `data/processed/foods.duckdb` | P1 | ✅ |
| N-02-08 | Stats + quality report | `data/processed/stats.json` | P1 | ✅ |

---

## 1. Schema (N-02-01)

- [x] Pydantic `FoodRecord` matching README schema
- [x] Enum `FoodSource = Literal["taco", "tbca", "fdc", "off"]`
- [x] Helper: `normalize_name(name: str) -> str`
- [x] Helper: `make_id(source, native_id) -> str`
- [x] Unit tests for schema validation (`tests/test_schema.py`)

---

## 2. TACO parser (N-02-02)

- [x] Map TACO Excel columns → FoodRecord (sheet `CMVCol taco3`, header rows 0–1)
- [x] Handle category rows vs food rows
- [x] Negative trace values → null
- [x] Set `language=pt-BR`, `serving_basis=100g`, `source_url` = NEPA URL
- [x] **Golden test:** Arroz, tipo 1, cozido → 128.26 kcal (TACO 4th ed white rice equivalent)
- [x] **Golden test:** banana prata crua → 98.25 kcal
- [x] Output: `data/processed/taco.parquet` (597 rows)

---

## 3. FDC parser (N-02-03)

- [x] Map FDC nutrient IDs: 1008, 1003, 1005, 1004, 1079, 1093, 1063
- [x] Parse Foundation Foods + Branded
- [x] Set `language=en`, `description` → `name`
- [x] Set `source_url` = https://fdc.nal.usda.gov/
- [x] Output: `data/processed/fdc.parquet` (2,051,573 rows)

---

## 4. OFF parser (N-02-04)

- [x] Read Parquet via DuckDB (no full RAM load)
- [x] Filter Brazil at parse: `list_contains(countries_tags, 'en:brazil')`
- [x] Extract nutriments array (`energy-kcal`, `proteins`, etc.)
- [x] Map product_name, brands, code, allergens_tags
- [x] Output: `data/processed/off-brazil.parquet` (32,996 rows)

---

## 5. Merge (N-02-05)

- [x] Concat → `data/processed/foods.parquet`
- [x] Enforce unique `id` — no duplicates
- [x] `data/processed/source_counts.json`

---

## 6. Validation (N-02-06)

- [x] `validate.py` runs BR-NORM-001…004
- [x] TACO row count 597 (within 500–700)
- [x] OFF Brazil count 32,996
- [x] `stats.json` null rates per source
- [x] Golden rows within ±1% tolerance

---

## 7. DuckDB (N-02-07)

- [x] `foods.duckdb` with indexes on `source`, `name_normalized`
- [x] Sample query: `ILIKE '%arroz%'` documented in validate log

---

## 8. Quality report (N-02-08)

- [x] `stats.json`: 2,085,166 total rows
- [x] Top 20 categories listed
- [x] `energy_without_macros` flagged
- [x] Manual spot-check: 5 random TACO rows logged

---

## Gate

- [x] All P0 tasks complete
- [x] Golden TACO tests green
- [x] `foods.parquet` > 100k rows (2,085,166)
- [x] Ready for [Phase 3](../03-vector-db-rag/TASKS.md) and [Phase 4](../04-finetuning-dataset/TASKS.md)

**Effort estimate:** 5–7 days
