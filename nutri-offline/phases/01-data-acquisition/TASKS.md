# Phase 1 tasks — Data acquisition

> **ID:** N-01 · Raw data download  
> **Quality gate:** All P0 sources downloaded; `manifest.json` complete; DuckDB/pandas smoke read  
> **Status:** Done (2026-06-27)  
> **Depends on:** [Phase 0](../00-hardware-environment/TASKS.md)

---

## Owner decisions (resolve before N-01-01)

| Decision | Options | Status |
|----------|---------|--------|
| **OFF format** | Parquet (recommended) · CSV.gz · JSONL.gz | ✅ Parquet (HF export) |
| **FDC scope** | Foundation + Branded (recommended) · Foundation only | ✅ Foundation + Branded |
| **TBCA in v1** | Include as complement · defer to v2 | ✅ Defer — no bulk API |
| **OFF geographic filter** | Brazil-only at download · filter at normalize | ✅ Brazil-only at normalize |
| **FDC API key** | Store in `nutri-offline/.env` (gitignored) | ⬜ Optional for incremental updates later |

---

## 0. Prerequisites

- [x] Phase 0 complete — Python env + directory layout
- [x] Read [OFFICIAL-REFERENCE.md](OFFICIAL-REFERENCE.md)
- [x] Read [README.md](README.md)
- [x] ≥ 50 GB free disk confirmed (440 GB free on /data)

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-01-01 | Download TACO official Excel | `data/raw/taco/` | P0 | ✅ |
| N-01-02 | Download TACO community CSV (backup) | `data/raw/taco/` | P1 | ✅ |
| N-01-03 | Download FDC bulk datasets | `data/raw/fdc/` | P0 | ✅ |
| N-01-04 | Download Open Food Facts Parquet | `data/raw/off/` | P0 | ✅ |
| N-01-05 | Explore TBCA export options | `data/raw/tbca/` | P1 | ✅ |
| N-01-06 | Build download scripts | `scripts/download/` | P0 | ✅ |
| N-01-07 | Create manifest.json | checksums + provenance | P0 | ✅ |
| N-01-08 | Smoke read all sources | DuckDB / pandas | P0 | ✅ |

---

## 1. TACO download (N-01-01, N-01-02)

- [x] Download official Excel from https://nepa.unicamp.br/publicacoes/tabela-taco-excel/
- [x] Save to `data/raw/taco/taco-oficial.xlsx`
- [x] Log download URL + date in manifest
- [x] Optional: community CSV from https://github.com/machine-learning-mocha/taco
- [x] Smoke test: 695 rows in `CMVCol taco3` sheet (~597 in community alimentos.csv)
- [x] Sheet names documented: `CMVCol taco3`, `AGtaco3`, `Aminoácidos TACO3`

---

## 2. FoodData Central bulk (N-01-03)

- [x] Visit https://fdc.nal.usda.gov/download-datasets/
- [x] Download Foundation Foods CSV (release 2025-04-24)
- [x] Download Branded Foods CSV (release 2025-04-24)
- [x] Save to `data/raw/fdc/` with version date in filename
- [ ] Register for API key at https://fdc.nal.usda.gov/api-key-signup/ — optional for Phase 1
- [x] Smoke test: Foundation `food.csv` 74,175 rows; nutrient columns present
- [x] Document FDC nutrient ID mapping — deferred detail to Phase 2 normalization

---

## 3. Open Food Facts (N-01-04)

- [x] Download Parquet from Hugging Face (official simplified export)
- [x] Save to `data/raw/off/food.parquet` (7.6 GB)
- [x] Smoke test with DuckDB: **4,571,176 rows**
- [x] Columns confirmed: `product_name`, `brands`, `countries_tags` (among others)
- [x] Full JSONL avoided (~43 GB decompressed)

---

## 4. TBCA complement (N-01-05) — optional P1

- [x] Explore https://www.tbca.net.br/ — web-only, no bulk export
- [x] Document access method in `data/raw/tbca/access-notes.json`
- [x] Defer full TBCA ingest — TACO + FDC + OFF sufficient for v1

---

## 5. Download scripts (N-01-06)

- [x] `scripts/download/fetch_taco.py`
- [x] `scripts/download/fetch_fdc_bulk.py`
- [x] `scripts/download/fetch_openfoodfacts.py`
- [x] `scripts/download/run_all.py`
- [x] All scripts log to `logs/download-YYYY-MM-DD.log`
- [x] Idempotent: skip if file exists and checksum matches manifest

---

## 6. Manifest (N-01-07)

- [x] Create `data/raw/manifest.json` with 7 sources (TACO official + 3 community + FDC ×2 + OFF)
- [x] Include license + attribution string per source

---

## 7. Smoke read gate (N-01-08)

- [x] TACO: 695 foods in primary sheet (within ~500–700 target)
- [x] FDC Foundation: 74,175 rows in `food.csv`
- [x] OFF: 4,571,176 rows — DuckDB query without full RAM load
- [x] All files non-zero size; SHA256 in manifest
- [x] Ready for [Phase 2 — Normalization](../02-data-normalization/TASKS.md)

**Disk usage (raw):** ~8.0 GB total

---

## Gate

- [x] All P0 tasks complete
- [x] manifest.json complete (local, gitignored)
- [x] Disk usage logged — well under 80 GB raw cap

**Effort estimate:** 1–2 days (mostly download time for OFF/FDC)
