# Phase 11 tasks — Full catalog index + robust benchmark

> **ID:** N-11 · **Quality gate:** G-COV + G-RET + G-DOM + G-PERF + R-FULL-10  
> **Status:** In progress — Blocks 0, D (partial), E done · Block A (overnight build) pending  
> **Depends on:** [Phase 2](../02-data-normalization/TASKS.md), [Phase 3](../03-vector-db-rag/TASKS.md), [Phase 5](../05-finetuning-training/TASKS.md), [Phase 7](../07-app-integration/TASKS.md)

---

## Readiness overview

| Block | Purpose | Status |
|-------|---------|--------|
| [0 — Prerequisites](#block-0--prerequisites-n-11-00) | Parquet stats, disk, TBCA gap | ✅ smoke |
| [A — Full index build](#block-a--full-index-build-n-11-01--n-11-05) | `--scope all` LanceDB | ⬜ overnight |
| [B — Coverage & retrieval](#block-b--coverage--retrieval-benchmarks-n-11-10--n-11-15) | G-COV + G-RET harness | 🟡 G-COV scaffold |
| [C — Domain eval v2](#block-c--domain-eval-v2-n-11-20--n-11-24) | 200-prompt eval | ⬜ |
| [D — App integration](#block-d--app-integration-n-11-30--n-11-32) | Health + wiring | 🟡 partial |
| [E — Documentation](#block-e--documentation-n-11-40--n-11-42) | Promote phase + gates | ✅ |

---

## Task list

| ID | Task | Folder / notes | Priority | Status |
|----|------|----------------|----------|--------|
| N-11-00a | Confirm `foods.parquet`; refresh `source_counts.json` | `check_full_catalog_prereqs.py` | P0 | ✅ |
| N-11-00b | Document TBCA gap | README, prereq script | P2 | ✅ |
| N-11-00c | Disk ≥15 GB under `indexes/` | prereq check | P0 | ✅ |
| N-11-01 | Build full index | `build_index_v2.py --scope all --device cuda` | P0 | ⬜ |
| N-11-02 | Rebuild aliases for full scope | `ensure_aliases()` in build | P0 | ⬜ |
| N-11-03 | `metadata.json` per-source breakdown | `build_index_v2.py` | P0 | ✅ |
| N-11-04 | Optional int8 index if float >10 GB | `--quantize int8` | P1 | ⬜ |
| N-11-05 | Source-aware hybrid boost at 2M scale | `hybrid_search.py` | P0 | ⬜ |
| N-11-10 | `benchmark_coverage.py` + unit tests | `scripts/rag/`, `tests/test_full_catalog_coverage.py` | P0 | ✅ |
| N-11-11 | `benchmark_retrieval.py` + stratified sampler | `scripts/rag/` | P0 | ⬜ |
| N-11-12 | CI-fast gate fixture (~200 queries) | `tests/fixtures/retrieval_gate_sample.jsonl` | P0 | ⬜ |
| N-11-13 | `benchmark_latency.py` | `scripts/rag/` | P1 | ⬜ |
| N-11-14 | Generate retrieval query corpus | `generate_retrieval_corpus.py` | P0 | ⬜ |
| N-11-15 | `validate-nutri-full-catalog.sh` | repo root | P0 | ✅ |
| N-11-20 | 200-prompt fixture | `domain_eval_v2_200.jsonl` | P0 | ⬜ |
| N-11-21 | Variant disambiguation in `eval_scoring.py` | training | P0 | ⬜ |
| N-11-22 | `eval_domain.py --fixture v2 --require-rag` | training | P0 | ⬜ |
| N-11-23 | Gate fixture v2 (25 prompts) | `domain_eval_gate_v2.jsonl` | P0 | ⬜ |
| N-11-24 | Markdown benchmark report v2 | reporter | P1 | ⬜ |
| N-11-30 | `NUTRI_INDEX_SCOPE` + orchestrator uses full index | `app_paths.py`, env | P0 | 🟡 env only |
| N-11-31 | `/health` exposes `index_records`, `index_scope` | `runtime_router.py` | P1 | ✅ |
| N-11-32 | R-FULL-10 smoke script | `test_r_full_10.py` | P0 | ✅ |
| N-11-40 | Phase README + TASKS | `phases/11-full-catalog-index/` | P1 | ✅ |
| N-11-41 | `docs/FULL-CATALOG-INDEX.md` | docs | P1 | ✅ |
| N-11-42 | Row in `IMPLEMENTATION-PLAN.md` | root | P1 | ✅ |

---

## Block 0 — Prerequisites (N-11-00)

- [x] `check_full_catalog_prereqs.py` writes `data/processed/source_counts.json`
- [x] TBCA gap documented (not in parquet)
- [x] Disk check under `indexes/`

---

## Block A — Full index build (N-11-01 … N-11-05)

- [ ] Overnight: `python scripts/rag/build_index_v2.py --scope all --device cuda`
- [x] `source_counts` in `metadata.json` (N-11-03)
- [ ] Hybrid boost audit at 2M scale (N-11-05)

---

## Block B — Coverage & retrieval benchmarks (N-11-10 … N-11-15)

- [x] G-COV script + unit tests + seed fixture
- [x] Gate script (`smoke` + `full` modes)
- [ ] G-RET retrieval benchmark (N-11-11 … N-11-14)

---

## Block C — Domain eval v2 (N-11-20 … N-11-24)

- [ ] All tasks pending — keep Phase 5 50-prompt gate for training loop until N-11-22 lands

---

## Block D — App integration (N-11-30 … N-11-32)

- [x] `/health` returns `index_scope`, `index_records`, `index_source_counts`
- [x] R-FULL-10 smoke (`test_r_full_10.py`; RF03/RF04 skip on v1)
- [x] Admin runtime router + desktop rule-engine parity (Phase 7 N-07-11…13)
- [ ] Flip default to `NUTRI_INDEX_SCOPE=all` after strict gate passes

---

## Block E — Documentation (N-11-40 … N-11-42)

- [x] Promoted from `.local/nutri-phase-11-full-catalog-index.md`
- [x] `docs/FULL-CATALOG-INDEX.md`
- [x] `IMPLEMENTATION-PLAN.md` phase table

---

## Exit criteria (Phase 11 complete)

- [ ] G-COV 100% row parity (`scope=all`)
- [ ] G-RET gate fixture recall targets met
- [ ] G-DOM gate v2 ≥96% row pass, 0% unknown hallucination
- [ ] G-PERF p95 <300 ms
- [ ] R-FULL-10 10/10 on full index
- [x] Smoke gate green: `./scripts/validate-nutri-full-catalog.sh smoke`

---

## Progress

| Date | Milestone | Notes |
|------|-----------|-------|
| 2026-06-29 | Local plan drafted | `.local/nutri-phase-11-full-catalog-index.md` |
| 2026-06-29 | Phase promoted | README + TASKS + G-COV scaffold + smoke gate |
| — | Full index build | Run N-11-01 overnight, then `./scripts/validate-nutri-full-catalog.sh full` |
