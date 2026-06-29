# Full catalog index — Phase 11 reference

> **Phase:** [N-11](../phases/11-full-catalog-index/README.md) · **Gate:** [validate-nutri-full-catalog.sh](../../scripts/validate-nutri-full-catalog.sh)

---

## Index scopes

| Scope | SQL filter | Rows (approx.) | Use case |
|-------|------------|----------------|----------|
| `v1` | TACO + OFF-BR + FDC Foundation | ~108k | Default production; fast build |
| `all` | Every row in `foods.parquet` | ~2.08M | Branded FDC, long-tail search |

Build:

```bash
cd nutri-offline && source venv/bin/activate
export HF_HOME="$(pwd)/models/base"

# v1 (current default)
python scripts/rag/build_index_v2.py --scope v1 --device cuda

# full catalog (Phase 11 — overnight)
python scripts/rag/build_index_v2.py --scope all --device cuda
```

`metadata.json` records `scope`, `record_count`, and `source_counts`.

---

## Estimates (`scope=all`)

| Metric | v1 (actual) | all (estimate) |
|--------|-------------|----------------|
| Rows | 107,768 | 2,085,166 |
| Index disk | ~441 MB | ~8–9 GB float |
| Build time (CUDA) | ~16 min | ~5–8 h |
| Hybrid p95 target | <100 ms | <300 ms |

Mitigations if disk or latency fail: int8 vectors, source-split tables, hybrid boost tuning (N-11-04, N-11-05).

---

## Benchmark layers

### G-COV — coverage (`benchmark_coverage.py`)

| ID | Check |
|----|-------|
| G-COV-01 | `record_count` == parquet count for index scope |
| G-COV-02 | Per-source counts match parquet |
| G-COV-03 | Random ID sample → same `energy_kcal` in index |
| G-COV-04 | No empty `name` in spot sample |

### G-RET — retrieval *(pending N-11-11)*

Stratified queries across TACO, OFF, FDC foundation, FDC branded, aliases, negatives.

### G-DOM — domain LLM v2 *(pending N-11-20)*

200 prompts with RAG-on production path; 25-prompt CI gate.

### G-PERF — latency *(pending N-11-13)*

p50/p95 hybrid search, cold start, build resumability.

---

## R-FULL-10 smoke

| ID | Query | Expected |
|----|-------|----------|
| RF01 | `arroz 100g` | TACO lookup |
| RF02 | `iogurte vigor 170g` | OFF lookup |
| RF03 | `cheerios` | FDC branded *(skip on v1)* |
| RF04 | `mcdonald's big mac` | FDC branded *(skip on v1)* |
| RF05 | `100g frango grelhado` | TACO peito |
| RF06 | `nutrizxyabc 100g` | not found |
| RF07 | `barcode 7891000100103` | OFF if present |
| RF08 | compare arroz/feijão | compare mode |
| RF09 | mais leve que arroz | substitute mode |
| RF10 | calorias uma banana | lookup + portion |

```bash
python scripts/app/test_r_full_10.py
```

---

## App wiring

After strict gate passes:

```bash
export NUTRI_INDEX_SCOPE=all   # documented; index path unchanged
bash scripts/app/start_chat.sh
curl -s 'http://127.0.0.1:8090/v1/nutri/health?runtime=desktop' | jq '.index_scope,.index_records'
```

Mobile pack unchanged — long-tail branded queries remain **desktop-only**.

---

## References

- [MOBILE-CAPABILITY-MATRIX.md](MOBILE-CAPABILITY-MATRIX.md)
- [README-RAG-V2.md](README-RAG-V2.md)
- [Phase 11 TASKS](../phases/11-full-catalog-index/TASKS.md)
