# Phase 11 — Full catalog index + robust benchmark

> **ID:** N-11 · **Status:** In progress (scaffold + smoke gate ✅ · full index build pending)  
> **Depends on:** [Phase 2](../02-data-normalization/TASKS.md), [Phase 3](../03-vector-db-rag/TASKS.md), [Phase 5](../05-finetuning-training/TASKS.md), [Phase 7](../07-app-integration/TASKS.md)  
> **Goal:** Index **every row** in `foods.parquet` (`--scope all`) and prove retrieval + assistant quality with a four-layer benchmark stronger than the 50-prompt LLM gate.

---

## Why Phase 11

Post-train v2 eval shows numeric variant failures when RAG is off. Production assumes RAG; today only **~5.2%** of parquet rows are searchable in the v1 desktop index (~107k / 2.08M). Phase 11 closes the gap for **FDC branded** and long-tail OFF without changing the mobile 200 MB pack.

| Surface | v1 (today) | Phase 11 target |
|---------|------------|-----------------|
| Desktop LanceDB | 107,768 rows (`--scope v1`) | **2,085,166** rows (`--scope all`) |
| Mobile pack | Curated subset | **Unchanged** — desktop authoritative for branded / long-tail |
| Domain eval | 50 prompts | **200+** + retrieval suite + coverage gate |

**Scope definition (BR-N11-001):**

```
GIVEN foods.parquet after Phase 2 merge
WHEN build_index_v2 runs with --scope all
THEN every row WHERE source IN ('taco','fdc','off') appears in LanceDB
AND metadata.json record_count equals DuckDB COUNT(*)
```

TBCA is **not in parquet** — tracked as N-11-00b. Do not claim 100% of *possible* Brazilian sources until TBCA is ingested (future Phase 12).

---

## Non-goals

| Item | Reason |
|------|--------|
| Full 2M rows on mobile | 200 MB cap; Phase 8 architecture stays |
| Re-train LLM on branded names | RAG + lookup ground numbers |
| Real-time OFF sync | Phase 1 cadence unchanged |

---

## Four-layer quality gate

| Layer | ID | Tool | CI mode |
|-------|-----|------|---------|
| Coverage | G-COV | `benchmark_coverage.py` | strict with `--require-scope all` |
| Retrieval | G-RET | `benchmark_retrieval.py` *(pending)* | gate fixture ~200 queries |
| Domain LLM | G-DOM | `eval_domain.py` v2 *(pending)* | 25-prompt gate |
| Performance | G-PERF | `benchmark_latency.py` *(pending)* | p95 <300 ms |

Regression smoke: **R-FULL-10** — `scripts/app/test_r_full_10.py` (branded cases skip until `scope=all`).

---

## Commands

```bash
# From repo root — smoke (passes on v1 index today)
./scripts/validate-nutri-full-catalog.sh smoke

# After overnight build — strict gate
cd nutri-offline && source venv/bin/activate
export HF_HOME="$(pwd)/models/base"
python scripts/rag/build_index_v2.py --scope all --device cuda   # N-11-01 (~5–8 h)
./scripts/validate-nutri-full-catalog.sh full

# Point app at full index after gate passes
export NUTRI_INDEX_SCOPE=all
bash scripts/app/start_chat.sh
```

See [docs/FULL-CATALOG-INDEX.md](../../docs/FULL-CATALOG-INDEX.md) for architecture, estimates, and benchmark targets.

---

## Task index

See [TASKS.md](TASKS.md) for N-11-00 … N-11-42 checklist.

---

## Relationship to other phases

| Phase | Interaction |
|-------|-------------|
| **3** RAG v2 | `build_index_v2.py --scope all` already exists — Phase 11 operationalizes it |
| **5** Training | Domain eval v2 supersedes 50-prompt gate for release |
| **7** App | Admin runtime router + rule-engine parity (N-11-30 partial) |
| **8–10** Mobile | No pack change; B20 stays mobile-only |
| **12** *(future)* | TBCA ingest → re-run N-11 |
