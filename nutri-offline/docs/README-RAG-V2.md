# RAG V2 — Performance, accuracy, and shorthand UX plan

> **Status:** Phase A done (2026-06-28) · **Parent:** [Phase 3](../phases/03-vector-db-rag/README.md) · [Phase 7](../phases/07-app-integration/README.md)  
> **Goal:** 10× faster responses, lighter runtime, and **correct macros from TACO / FDC / OFF** with intuitive input like `arroz 100g, carne 200g`.

---

## Why this plan exists

The current stack (LanceDB + bge-m3 + Qwen2.5-3B GGUF) already **vectorizes** ~107k foods and retrieves top-k at runtime (~60 ms warm). The bottleneck and quality issues are **not** missing vectors — they are **how we retrieve, rank, and answer**.

### Observed API behaviour (2026-06-28 logs)

| User input | Latency | Problem |
|------------|---------|---------|
| `arroz 100g` | **24.0 s** | Lists 5 different rice products; values inconsistent (248–450 kcal); **TACO not used**; LLM invents FDC URLs not present in RAG context |
| `arroz 100g, carne 200g` | **11.9 s** | Wrong food match (`CARNE AL JUGO con arroz`); **broken portion math** (992 kcal totals); treats “carne” as packaged dish |
| `Quantas calorias tem 100g de arroz branco cozido?` (full sentence) | **7.8 s** | OFF cited instead of TACO; 138 kcal vs TACO golden **128 kcal** |
| E2E S1 (explicit “segundo a TACO”) | **7.8 s** | ✅ Pass — TACO retrieved when user forces source |
| E2E S2 (frango vs ovo) | **15.2 s** | ✅ Pass but slow; OFF branded eggs/chicken instead of TACO generic |

**Baseline latency (smoke-test GGUF, `logs/inference-benchmark.json`):**

| Prompt type | LLM only |
|-------------|----------|
| Short | ~1.0 s |
| Medium | ~2.5 s |
| RAG context | ~3.8 s |

**End-to-end chat (fine-tuned v1 GGUF):** 8–24 s — dominated by LLM generation length and large prompts.

### Root causes

1. **Pure semantic search** — no source priority, no entity/portion parsing, no hybrid keyword match.
2. **LLM writes numbers** — even with RAG, the model paraphrases and drifts (URLs, rounding, wrong product).
3. **One-shot retrieval** — single embedding for the whole utterance; multi-food queries (`arroz 100g, carne 200g`) are not split.
4. **Heavy generation** — long free-form answers for simple lookups.
5. **Index naming gap** — TACO uses `Arroz, tipo 1, cozido`; users type `arroz 100g`.

---

## Target outcome

| Metric | Today (v1) | Target (v2) |
|--------|------------|-------------|
| Shorthand lookup (`arroz 100g`) | 8–24 s | **≤ 800 ms** (lookup path) |
| Multi-item (`arroz 100g, carne 200g`) | 12 s, wrong math | **≤ 1.2 s**, correct totals |
| Numeric accuracy vs source | ~70% (informal) | **≥ 95%** on golden set |
| Source correctness (generic BR food) | OFF often wins | **TACO / TBCA first** |
| VRAM at inference | ~2–3 GB (3B q4) | **≤ 2 GB** optional q3 / 1.5B route |
| User input style | Full PT-BR sentences | **`food portion` shorthand** |

**10× faster** = move **≥ 80% of lookup queries** to a **deterministic retrieval + template** path that skips the LLM entirely.

---

## Architecture V2 — Active retrieval orchestrator

```
User: "arroz 100g, carne 200g"
        │
        ▼
┌───────────────────┐
│ 1. Intent parser  │  → [{food:"arroz", g:100}, {food:"carne", g:200}]
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 2. Per-item       │  hybrid: vector + keyword + source boost
│    retrieval      │  → best record per item (TACO > TBCA > FDC > OFF)
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 3. Route decision │
└─────────┬─────────┘
          │
    lookup │                    reasoning
          ▼                          ▼
┌──────────────────┐      ┌──────────────────┐
│ 4a. Template     │      │ 4b. Slim LLM     │
│     renderer     │      │     (optional)   │
│ (answers.py)     │      │ compare / advice │
└─────────┬────────┘      └────────┬─────────┘
          │                          │
          └──────────┬───────────────┘
                     ▼
          Standardized markdown / table response
```

**Principle:** The LLM explains and compares; **the database owns numbers** (reuse Phase 4 `answers.py` formatting).

---

## Pillar 1 — Shorthand UX (`food + portion`)

### Input patterns to support

| Pattern | Example | Parsed |
|---------|---------|--------|
| food + mass | `arroz 100g` | arroz · 100g |
| food + mass (comma list) | `arroz 100g, carne 200g, ovo 1 un` | 3 items |
| implicit 100g | `arroz` | arroz · 100g (default) |
| branded hint | `iogurte vigor 170g` | brand filter → OFF |
| explicit source | `arroz cozido taco 100g` | source=taco |

### Standardized response format

Every lookup answer uses the same template (PT-BR):

```markdown
### Resumo nutricional

| Alimento | Porção | Fonte | kcal | Proteína | Carboidrato | Gordura |
|----------|--------|-------|------|----------|-------------|---------|
| Arroz, tipo 1, cozido | 100g | TACO (NEPA/UNICAMP) | 128 | 2.5g | 28.1g | 0.2g |
| Carne bovina, coxão mole, grelhada | 200g | TACO | 438 | 65.6g | 0g | 18.4g |
| **Total** | | | **566** | **68.1g** | **28.1g** | **18.6g** |

_Fontes: TACO (NEPA/UNICAMP). Valores calculados a partir dos dados indexados._
```

Optional one-line LLM summary **only when** user asks “é saudável?” / comparison — numbers still from table.

### Deliverables

| ID | Task | Path |
|----|------|------|
| RAG-V2-01 | Portion intent parser (regex + food lexicon) | `scripts/app/intent_parser.py` |
| RAG-V2-02 | Multi-item splitter | same module |
| RAG-V2-03 | Standard table renderer | `scripts/app/response_formatter.py` |
| RAG-V2-04 | Chat UI hint + examples | `scripts/app/static/chat.html` |

---

## Pillar 2 — Smarter retrieval (active DB search)

### 2.1 Source authority matrix (BR-RET-001)

| Query type | Priority order |
|------------|----------------|
| Generic Brazilian food (`arroz`, `feijão`, `banana`) | **TACO → TBCA → FDC foundation → OFF BR** |
| Branded product (`Vigor`, barcode) | **OFF BR → FDC** |
| US / generic international | **FDC foundation → OFF** |

Implement as **score boost** after vector search, not hard filter:

```python
boost = {"taco": 0.15, "tbca": 0.12, "fdc": 0.05, "off": 0.0}
final_score = cosine_score + boost[source] + keyword_match_bonus
```

### 2.2 Hybrid search

| Layer | Purpose |
|-------|---------|
| **Vector** (bge-m3 / lighter model) | Semantic similarity |
| **Keyword** (BM25 / LanceDB FTS / DuckDB LIKE) | Exact token match on `name` |
| **Alias index** | `arroz` → `Arroz, tipo 1, cozido` (curated + mined from TACO) |

### 2.3 Per-item retrieval loop

For `arroz 100g, carne 200g`:

1. Split → 2 queries (not one embedding for full string).
2. Retrieve top-3 per item with source boost.
3. Disambiguate: if top-2 scores within 0.03, pick TACO generic over OFF branded.
4. Scale macros with `answers.scale_nutrient()` (already in Phase 4).

### 2.4 Structured metadata in index

Extend LanceDB row:

```yaml
name_normalized: "arroz tipo 1 cozido"
aliases: ["arroz branco cozido", "arroz cozido"]
source_tier: 1  # 1=TACO/TBCA, 2=FDC, 3=OFF
is_generic: true
```

Rebuild index: `scripts/rag/build_index_v2.py`.

### Deliverables

| ID | Task |
|----|------|
| RAG-V2-05 | Source boost + reranker |
| RAG-V2-06 | Hybrid FTS + vector (LanceDB hybrid or DuckDB sidecar) |
| RAG-V2-07 | Food alias table (`data/processed/food_aliases.parquet`) |
| RAG-V2-08 | Per-item retrieval in orchestrator |
| RAG-V2-09 | Index v2 schema + rebuild gate |

---

## Pillar 3 — Deterministic lookup path (speed)

### When to skip the LLM

| Condition | Action |
|-----------|--------|
| Parsed as portion lookup only | Template answer — **no LLM** |
| All items matched with score ≥ threshold | Template + totals |
| User asks comparison with 2 matched items | Mini-prompt OR pure Python max() |
| Unknown food / low score | “Não encontrado” — **no invented numbers** (BR-DS-002) |
| Open-ended advice | Slim LLM with **pre-rendered table** in system context |

**Expected latency:** embed (~30 ms) + hybrid search (~20 ms) + render (~5 ms) ≈ **≤ 100 ms** warm.

### Reuse existing code

- `scripts/dataset/answers.py` — `macro_parts`, `scale_nutrient`, `generate_direct_lookup`
- `scripts/app/test_offline_e2e.py` — extend golden scenarios for shorthand

### Deliverables

| ID | Task |
|----|------|
| RAG-V2-10 | `LookupOrchestrator` with LLM bypass flag |
| RAG-V2-11 | Confidence gate (min score, source match) |
| RAG-V2-12 | API field `mode: "lookup" \| "llm" \| "auto"` |
| RAG-V2-13 | Benchmark script `scripts/app/benchmark_v2.py` |

---

## Pillar 4 — Lighter and faster inference

### 4.1 Embedding model options

| Model | Dims | Speed | Recommendation |
|-------|------|-------|----------------|
| BAAI/bge-m3 (current) | 1024 | Baseline | Keep for rebuild quality |
| **BAAI/bge-small-en-v1.5** + PT aliases | 384 | ~3× faster | **v2 runtime default** |
| intfloat/multilingual-e5-small | 384 | ~3× faster | Alternative A/B |

Run A/B on 50 golden queries before switching production embedder.

### 4.2 LLM slimming (when LLM is needed)

| Option | Size | Tradeoff |
|--------|------|----------|
| Qwen2.5-3B **q3_k_m** | ~1.4 GB | Faster, slight quality loss |
| Qwen2.5-3B **q4_k_m** (current) | ~1.8 GB | Baseline |
| Qwen2.5-**1.5B** Instruct q4 | ~1 GB | Reasoning-only route |

LLM settings for reasoning path:

```yaml
max_tokens: 128        # was 512
temperature: 0.3
top_p: 0.9
n_gpu_layers: 99       # keep
```

### 4.3 Context diet

- Inject **compact table** (5 rows × 6 cols) instead of prose `rag_context`.
- Cap RAG to **top-3** for lookup; **top-5** only for LLM reasoning.
- Stream tokens to chat UI (SSE) — perceived latency ↓ even if total similar.

### 4.4 Caching

| Cache | Key | TTL |
|-------|-----|-----|
| Query embedding | normalized text | session |
| Retrieval result | `(food, portion_g, source_pref)` | 24h |
| Full lookup answer | hash(items) | 24h |

Store: `indexes/cache/` or in-memory LRU in FastAPI.

### Deliverables

| ID | Task |
|----|------|
| RAG-V2-14 | Embedder A/B benchmark |
| RAG-V2-15 | Export q3_k_m GGUF + gate |
| RAG-V2-16 | Compact RAG context builder |
| RAG-V2-17 | SSE streaming in `/v1/nutri/chat/stream` |
| RAG-V2-18 | Response cache layer |

---

## Pillar 5 — Accuracy gates (business rules)

Document in domain layer style:

### BR-RET-001 — Source priority

```
GIVEN a generic Brazilian food query ("arroz 100g")
WHEN hybrid retrieval returns TACO and OFF candidates
THEN the selected record MUST prefer TACO if score within 0.05 of top OFF hit
```

### BR-RET-002 — Numeric grounding

```
GIVEN a lookup response
WHEN macros are displayed
THEN every number MUST come from retrieved record fields via scale_nutrient()
AND MUST NOT be LLM-generated
```

### BR-RET-003 — Multi-item independence

```
GIVEN "arroz 100g, carne 200g"
WHEN processing
THEN each item is retrieved independently
AND totals are computed in Python
```

### Golden test set (extend E2E)

| ID | Input | Expected source | Expected kcal (±2%) |
|----|-------|-----------------|---------------------|
| G1 | `arroz 100g` | TACO arroz tipo 1 cozido | 128 |
| G2 | `banana 100g` | TACO banana prata | ~98 |
| G3 | `arroz 100g, feijão 100g` | TACO both | sum correct |
| G4 | `nutrixyz 100g` | not found | no fabricated kcal |
| G5 | `iogurte vigor` | OFF branded | product-specific |

Gate script: `scripts/validate-nutri-rag-v2.sh`

---

## Implementation roadmap

### Phase A — Quick wins (3–5 days) ✅

No index rebuild required.

- [x] RAG-V2-01 … RAG-V2-04 — intent parser + table formatter + chat hints
- [x] RAG-V2-05 — source boost in existing `RagPipeline.search`
- [x] RAG-V2-10 — lookup bypass using `answers.py`
- [x] RAG-V2-11 — confidence gate (min score + name overlap)
- [x] RAG-V2-12 — API field `mode: "lookup" | "llm" | "auto"`
- [x] RAG-V2-16 — compact context
- [x] Reduce `max_tokens` to 128 for auto-LLM fallback

**Exit:** `arroz 100g` returns TACO table in **< 1 s** without LLM. Validated: ~65–90 ms lookup, 128 kcal TACO.

### Phase B — Hybrid retrieval (5–7 days)

- [ ] RAG-V2-07 — alias table from TACO names + manual seeds
- [ ] RAG-V2-06 — keyword + vector hybrid
- [ ] RAG-V2-08 — per-item retrieval loop *(basic loop shipped in Phase A; hybrid per-item in Phase B)*
- [ ] RAG-V2-09 — index v2 columns (`name_normalized`, `aliases`, `source_tier`)
- [ ] Golden gate G1–G5 *(G1–G4 pass in `tests/test_lookup_golden.py`; G5 branded OFF manual)*

**Exit:** shorthand multi-item queries correct on golden set.

### Phase C — Performance polish (3–5 days)

- [ ] RAG-V2-14 — smaller embedder + re-benchmark
- [ ] RAG-V2-15 — q3_k_m export optional profile
- [ ] RAG-V2-17 — SSE streaming in chat UI
- [ ] RAG-V2-18 — cache layer
- [ ] RAG-V2-13 — benchmark report → `logs/rag-v2-benchmark.json`

**Exit:** p95 lookup **≤ 800 ms**; p95 reasoning **≤ 3 s**; 10× vs current shorthand p95 (~12–24 s).

---

## File layout (new)

```
nutri-offline/
├── docs/
│   └── README-RAG-V2.md          ← this file
├── data/processed/
│   └── food_aliases.parquet      ← RAG-V2-07
├── scripts/
│   ├── app/
│   │   ├── intent_parser.py    ← RAG-V2-01
│   │   ├── response_formatter.py
│   │   ├── lookup_orchestrator.py
│   │   └── benchmark_v2.py
│   └── rag/
│       ├── build_index_v2.py
│       ├── hybrid_search.py
│       └── rerank.py
└── tests/
    ├── test_intent_parser.py
    └── test_lookup_golden.py
```

---

## Chat UI changes (intuitive shorthand)

Update placeholder and welcome text:

```
Exemplos:
  arroz 100g
  arroz 100g, carne 200g, salada 50g
  banana | feijão 80g
  iogurte vigor 170g
```

Show **table rendering** in chat (markdown → HTML) instead of prose blocks.

Add badge: `lookup` (fast, no LLM) vs `llm` (reasoning).

---

## Success checklist

- [x] `arroz 100g` → TACO table, **128 kcal**, **< 1 s**
- [x] `arroz 100g, carne 200g` → 2 rows + correct total, **< 1.5 s**
- [x] No hallucinated URLs or numbers on lookup path
- [x] E2E golden G1–G4 pass offline (`tests/test_lookup_golden.py`)
- [ ] Benchmark documents 10× improvement on lookup p95
- [ ] Phase docs updated; gate `validate-nutri-rag-v2.sh` in CI

---

## References

- [Phase 3 RAG](../phases/03-vector-db-rag/README.md) — current LanceDB + bge-m3
- [Phase 4 answers.py](../scripts/dataset/answers.py) — grounded formatting (reuse)
- [UC-Nutri-Query](UC-nutri-query.md) — BR-DS-001 / BR-DS-002
- [Chat UI](../scripts/app/static/chat.html)
- Logs: `logs/e2e-offline-*.json`, `logs/inference-benchmark.json`, `logs/nutri-app.log`

---

**Next step:** **Phase B** — alias table + hybrid FTS/vector search (`food_aliases.parquet`, `hybrid_search.py`).
