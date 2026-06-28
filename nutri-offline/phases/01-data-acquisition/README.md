# Phase 1 — Data acquisition

> **Status:** Done (2026-06-27)  
> **Parent:** [Phase 0](../00-hardware-environment/README.md) · [IMPLEMENTATION-PLAN.md](../../IMPLEMENTATION-PLAN.md)  
> **Goal:** Download all official nutrition datasets to `nutri-offline/data/raw/`.

---

## Objective

Acquire TACO, TBCA (complementary), FoodData Central bulk export, and Open Food Facts dump. Store raw files locally with provenance metadata — no transformation yet.

| Source | Format | Est. size | Priority |
|--------|--------|-----------|----------|
| TACO (NEPA/UNICAMP) | Excel / CSV | < 5 MB | P0 |
| TBCA (USP) | Web export / API | TBD | P1 |
| FoodData Central | CSV/JSON bulk | ~2 GB compressed | P0 |
| Open Food Facts | Parquet (recommended) or CSV.gz | ~0.9–7 GB compressed | P0 |

---

## Download strategy

```
scripts/download/
├── fetch_taco.py
├── fetch_tbca.py          # optional complement
├── fetch_fdc_bulk.py
├── fetch_openfoodfacts.py
└── manifest.json          # URLs, dates, checksums
```

Use DuckDB-friendly formats where available (Parquet for OFF). FDC requires free API key for incremental API access; bulk download preferred for offline pipeline.

---

## Out of scope

| Item | Reason |
|------|--------|
| Schema normalization | Phase 2 |
| Embedding generation | Phase 3 |
| Fine-tuning dataset | Phase 4 |

---

## Definition of done

- [x] TACO official file downloaded with source URL logged
- [x] FDC bulk dataset downloaded (Foundation + Branded, release 2025-04-24)
- [x] Open Food Facts Parquet downloaded (4.57M rows)
- [x] `manifest.json` records URL, download date, file size, SHA256
- [x] All files readable by DuckDB or pandas smoke test

**Manifest:** `nutri-offline/data/raw/manifest.json`  
**Smoke read log:** `nutri-offline/logs/smoke-read-sources.log`  
**Repo gate:** [scripts/validate-nutri-data-acquisition.sh](../../../scripts/validate-nutri-data-acquisition.sh)

---

**References:** [TASKS.md](TASKS.md) · [OFFICIAL-REFERENCE.md](OFFICIAL-REFERENCE.md)
