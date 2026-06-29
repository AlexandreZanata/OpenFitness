# NutriOffline — Semantic nutrition engine (v2 proposal)

> **Status:** Phase 9 in progress (N-09-01–03, N-09-05 ✅) · **Author:** product/architecture review  
> **Context:** Phase 8 mobile pack works (≤200 MB, ~37 MB artifact) but retrieval quality gaps come from **normalization**, not model size.  
> **Recommendation:** Do **not** invest further in classic RAG as the primary mechanism. Invest in a **specialized semantic engine** with structured lookup at the end.

---

## Core thesis

| Wrong assumption | Correct assumption |
|------------------|-------------------|
| The small model should “know” TACO macros | The model should **understand the question** only |
| One embedding per food row is enough | One food → **many semantic surfaces** (aliases, category, prep, regional names) |
| Vector search replaces a database | Vector search **resolves ambiguity**; SQLite/JSON holds **ground truth** |
| RAG context + LLM for NL queries | NL → **intent** → **normalized entity** → **deterministic nutrient read** |

User questions are mostly **structured queries in natural language**, not open-ended reasoning.

Examples that fail today for the **wrong reason**:

| User input | Should resolve to | Failure mode today |
|------------|-------------------|-------------------|
| `100g de arror` | `arroz` + 100g lookup | Typo not corrected → miss or wrong OFF hit |
| `carne vermelha` | `patinho` / `acém` / `contra-filé` (disambiguate) | Generic embedding → wrong cut or FDC noise |
| `uma manga inteira` | mango ~230g → scale macros | Only understands `100g`; “inteira” ignored |
| `pão francês` | same entity as `cacetinho`, `pão de sal` | Alias gap |

These are **normalization + ontology + portion rules**, not “smarter LLM”.

---

## Target architecture

```
                    User question (PT-BR)
                            │
                            ▼
              ┌─────────────────────────────┐
              │  Intent parser (rules +     │
              │  optional tiny classifier     │
              │  ≤15 MB, no macro memory)     │
              └─────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
   Structured query path              Open question
   (lookup / compare /                (recommendation,
    substitute / portion)               coaching — out of
            │                           scope or desktop LLM)
            ▼
   ┌────────────────────────────────────────────┐
   │ Layer 1–3: normalize token                 │
   │   spell-fix → synonyms → ontology walk     │
   └────────────────────────────────────────────┘
            │
            ▼
   ┌────────────────────────────────────────────┐
   │ Layer 4: semantic index (vectors)          │
   │   resolve entity_id among candidates       │
   │   (not “generate answer from chunks”)      │
   └────────────────────────────────────────────┘
            │
            ▼
   ┌────────────────────────────────────────────┐
   │ Layer 5: rules                             │
   │   household portions, colher/xícara,       │
   │   “inteira”, multi-item totals             │
   └────────────────────────────────────────────┘
            │
            ▼
   ┌────────────────────────────────────────────┐
   │ Structured store (SQLite)                  │
   │   TACO/TBCA/OFF row by id → scale_nutrient │
   └────────────────────────────────────────────┘
            │
            ▼
              Template answer (sources cited)
```

**AI role:** understand intent + disambiguate entity.  
**Database role:** every number.  
**Vectors role:** find the right row when text diverges from canonical name.

---

## Five layers (detailed)

### Layer 1 — Orthographic correction

Lightweight, deterministic first pass (no ML required for v1):

```
arror   → arroz
frangu  → frango
manga inteira → manga (+ portion hint "inteira")
```

Implementation options (pick one, stay ≤1 MB):

- SymSpell / BK-tree on normalized TACO + alias lexicon
- Edit distance against top 5k query tokens from logs
- Character n-gram index for mobile keyboard typos

**Business rule BR-NORM-001:** correction only applies when edit distance ≤2 and candidate exists in lexicon.

---

### Layer 2 — Synonyms

Bidirectional map: colloquial → canonical record id(s).

```
carne vermelha → { patinho, acém, alcatra, coxão mole, ... }
pão francês    → { pão, francês, cacetinho, pão de sal, ... }
```

Source:

- Manual seeds (high-value BR terms)
- Mined from TACO `name` + `name_normalized`
- `food_aliases.parquet` (already exists for desktop RAG V2)

**Difference from today:** aliases are not optional boost — they are the **primary** resolution path before vectors.

**Business rule BR-NORM-002:** colloquial multi-word phrases (`cacetinho`, `carne vermelha`) resolve via `synonyms.db` before vector search; ambiguous groups use a documented default record with label.

---

### Layer 3 — Ontology

Typed hierarchy for disambiguation and compare/substitute:

```
Meat
├── Bovine
│   ├── Patinho
│   ├── Alcatra
│   └── Acém
├── Poultry
│   └── Chicken → { breast, thigh, ... }
├── Fish
└── Pork
```

When user says `carne vermelha`:

1. Walk ontology → candidate set (all bovine cuts in pack)
2. If multiple macros differ → ask **one** clarify question OR pick default (e.g. `patinho`) with explicit label in answer

Storage: `config/semantic/food_ontology.json` (~50–100 KB).

**Business rule BR-NORM-003:** category phrases resolve through the ontology when the synonym layer has no exact match; ambiguous groups attach a clarify note to the lookup footer.

---

### Layer 4 — Multi-surface embeddings

**Do not** embed only canonical TACO name once.

Per food record, index **K semantic documents** (target K ≈ 20–50 for TACO tier A):

| Surface type | Example text anchored to `taco:314` |
|--------------|-------------------------------------|
| Canonical | `Arroz branco cozido` |
| Alias | `arroz`, `arroz comum`, `rice` |
| Category | `cereal`, `almoço`, `carboidrato` |
| Preparation | `cozido`, `sem óleo` |
| Regional | (manual) |
| FAQ-style | `quantas calorias tem arroz` |

Index row shape:

```json
{
  "record_id": "taco:314",
  "surface_id": "taco:314:alias:arroz",
  "surface_kind": "alias",
  "search_text": "arroz branco cozido arroz comum",
  "vector": "int8[384]"
}
```

**Scale math (TACO tier A only):**

- 597 foods × 40 surfaces ≈ **24k vectors**
- int8 384-dim ≈ 384 B/vector → ~9 MB vectors + metadata well inside 90 MB budget

Also index **intent prototypes** (separate small table, not food):

```
"quantas calorias"     → intent_calories
"quanto de proteína"   → intent_protein
"qual tem mais"        → intent_compare
"opção mais leve"      → intent_substitute
```

These can be regex today (Phase 8) and embedding prototypes later for typo-tolerant intent.

---

### Layer 5 — Rules engine (portions & units)

Household portion table (JSON/SQLite, ~200–500 rows):

| Food | Unit | Grams |
|------|------|-------|
| banana prata | 1 small | 65 |
| banana prata | 1 medium | 86 |
| banana prata | 1 large | 120 |
| mango | 1 medium whole | 230 |
| apple | 1 medium | 130 |

Rule pipeline:

```
"uma manga inteira"
  → detect unit: inteira + food: manga
  → portion_g = 230
  → lookup(record_id, 230g)
  → scale_nutrient()
```

Extend existing `PORTION_PATTERN` + NL patterns in `intent_parser.py`; **never** let templates invent grams.

**Business rule BR-PORT-001:** household weights must cite source (`TACO portion table` / `manual BR default`) in debug metadata.

**Business rule BR-PORT-002:** article-only (`um|uma|1 <food>`) or bare-food phrases (no explicit `Ng`) apply the entry `default_unit` from `household_portions.json`; explicit gram portions in the source phrase are never overridden. Aliases (e.g. `cacetinho` → `pao frances`) share the same default unit table.

Example pipeline:

```
"Quantas calorias tem uma banana?"
  → NL extract food: "uma banana"
  → default_unit: media → portion_g = 86
  → lookup(taco:182, 86g) → ~84 kcal

"100g banana"
  → PORTION_PATTERN present → keep 100g (no household override)
```

---

## Enriched food record (build-time schema)

Canonical JSON per TACO row (stored in SQLite, not generated at runtime):

```json
{
  "id": "taco:314",
  "nome": "Arroz, branco, cozido",
  "apelidos": ["arroz", "arroz branco", "arroz cozido", "arroz comum"],
  "categoria": "cereals",
  "familia_ontologia": "cereal.grain.rice",
  "tags": ["carboidrato", "almoço", "brasileiro"],
  "porcoes_caseiras": [
    { "unidade": "1 colher de sopa", "gramas": 25 },
    { "unidade": "1 xícara", "gramas": 160 }
  ],
  "superficies_busca": [
    { "kind": "alias", "text": "arroz" },
    { "kind": "faq", "text": "quantas calorias tem arroz" }
  ],
  "macros_100g": {
    "energy_kcal": 128,
    "protein_g": 2.5,
    "carbohydrate_g": 28.1,
    "fat_g": 0.2
  }
}
```

Build pipeline expands this into:

- `food_meta` (SQLite) — one row per record
- `food_surfaces` — many rows per record for FTS + vectors
- `aliases` — flat fast path

---

## Semantic expansion: 600 → 30k–50k documents

| Source | Records | Surfaces/record | Total surfaces |
|--------|---------|-----------------|----------------|
| TACO A | ~597 | 40 | ~24k |
| TBCA B | ~500 | 30 | ~15k |
| OFF tier C | 8k | 3 (name, brand, barcode) | ~24k |
| Intent prototypes | — | 50 | 50 |
| **Total** | | | **~63k** (tune OFF down if needed) |

Still fits mobile budget if:

- OFF surfaces stay keyword-heavy (FTS) with fewer vectors
- TACO/TBCA get full multi-surface vectors
- int8 quantization + sqlite-vec

---

## What to keep from Phase 8 (already built)

| Component | Keep? | Role in v2 |
|-----------|-------|------------|
| `intent_parser` + compare/substitute | ✅ | Layer 0 intent — extend, don’t replace |
| `mobile_search.py` hybrid scoring | ✅ | Becomes layer 4 resolver |
| `scale_nutrient()` / BR-RET-002 | ✅ | Final numeric step |
| `CompareEngine` / `SubstituteEngine` | ✅ | Rule templates after entity resolution |
| `nutri-mobile.pack` builder | ✅ | New manifest sections for surfaces |
| bge-small ONNX embedder | ✅ | Encode query + surface texts at build; query-only at runtime |
| LanceDB desktop index | ✅ desktop only | Unchanged |
| LLM 3B GGUF | ✅ desktop only | Only for truly open questions |

## What to de-emphasize

| Component | Action |
|-----------|--------|
| “RAG context → LLM” for factual macros | Remove from mobile; already done in Phase 8 |
| Single `search_text` embedding per row | Replace with multi-surface index |
| Raw embedding of user typo | Always run layer 1–3 before vector search |
| Growing OFF long-tail in pack | Keep tier C; rely on ontology for generics |

---

## Proposed implementation phases (after N-08)

| ID | Block | Deliverable | Est. |
|----|-------|-------------|------|
| N-09-01 | Spell-fix lexicon | `scripts/mobile/spell_normalize.py` + tests | 2d | ✅ |
| N-09-02 | Synonym graph v2 | Expand `food_aliases` + `synonyms.db` | 3d | ✅ |
| N-09-03 | Ontology | `config/semantic/food_ontology.json` + resolver | 3d | ✅ |
| N-09-04 | Multi-surface builder | `build_semantic_surfaces.py` → 24k rows | 5d | ✅ |
| N-09-05 | Household portions | `config/semantic/household_portions.json` + rules | 3d | ✅ |
| N-09-06 | Resolver pipeline | `SemanticResolver` replaces direct `mobile_search` entry | 4d | ✅ |
| N-09-07 | Pack v2 + gate | Rebuild pack; golden set includes typo/portion cases | 2d | ✅ |
| N-09-08 | Optional intent embedder | 50 prototype vectors if regex < 90% | 3d | ✅ skip |

**Exit criteria:**

- [x] `arror` → arroz 100g TACO 128 kcal (N-09-01)
- `carne vermelha` → plausible bovine cut with source label
- [x] `uma manga inteira` → kcal scaled to ~230g (N-09-05)
- `pão francês` / `cacetinho` → same canonical bread row
- p95 latency still ≤500 ms on mid-range CPU (see `logs/semantic-v2-benchmark.json`)
- Pack still ≤200 MB

---

## Size budget (v2 estimate)

| Component | v1 actual | v2 estimate |
|-----------|-----------|-------------|
| Vector index | ~20 MB | 35–55 MB (more surfaces, still int8) |
| Metadata + FTS | ~2 MB | 8–12 MB (surfaces + ontology) |
| Aliases + synonyms | in lexicon | 3–5 MB |
| Embedder ONNX | 34 MB | 34 MB (unchanged) |
| Household portions + rules JSON | — | <1 MB |
| Headroom | large | 20+ MB |

---

## Example end-to-end flows

### Flow A — typo shorthand

```
IN:  "100g de arror"
L1:  arror → arroz
L2:  arroz → taco:314 (alias hit)
L5:  portion_g = 100
DB:  scale(128 kcal) → 128
OUT: table row TACO 128 kcal
```

### Flow B — category phrase

```
IN:  "carne vermelha 200g"
L2:  → ontology bovine cuts
L4:  vector + alias rank → patinho (default policy)
L5:  portion_g = 200
OUT: macros from patinho row × 2
```

### Flow C — household unit

```
IN:  "Quantas calorias tem uma manga inteira?"
INT: intent_calories + portion hint
L5:  manga + inteira → 230g
L4:  resolve mango record
OUT: kcal for 230g, cite TACO + portion table
```

### Flow D — compare (no LLM)

```
IN:  "Qual tem mais proteína: frango ou ovo?"
INT: intent_compare, field=protein
L4:  resolve both entities
ENG: CompareEngine
OUT: winner + grounded values
```

---

## Relation to “100–200 MB intent model”

Optional **second** small model (DistilBERT multilingual INT8, ≤15 MB) only if:

- Regex + prototype embeddings fall below 90% on `mobile_nl_intents.jsonl`
- Inputs: user utterance → intent class + slot extraction (`food`, `portion`, `field`)
- **Never** used to output kcal numbers

Phase 8 already proves regex + rules cover 95% NL parity on a curated set — **exhaust normalization first**, add classifier only if metrics force it.

---

## Promotion checklist

- [x] Add `nutri-offline/docs/SEMANTIC-ENGINE-V2.md` (copy + refine)
- [x] Create `phases/09-semantic-engine/README.md` + `TASKS.md`
- [x] Add golden tests: typo (`tests/fixtures/spell_corrections.jsonl`)
- [ ] Add golden tests: ontology, household portions
- [ ] Update `MOBILE-CAPABILITY-MATRIX.md` query types Q11+
- [x] Bump `pack.manifest.json` `schema_version` to 2

---

## References (current codebase)

- Phase 8 pack: `nutri-offline/phases/08-mobile-pack/`
- Intent parser: `nutri-offline/scripts/app/intent_parser.py`
- Mobile search: `nutri-offline/scripts/mobile/mobile_search.py`
- Aliases desktop: `nutri-offline/scripts/rag/build_food_aliases.py`
- Spell-fix Layer 1: `nutri-offline/scripts/mobile/spell_normalize.py`
- Synonym Layer 2: `nutri-offline/scripts/mobile/synonym_resolver.py`
- Ontology Layer 3: `nutri-offline/scripts/mobile/ontology_resolver.py`
- Semantic pipeline (layers 1–3): `nutri-offline/scripts/mobile/semantic_resolver.py`
- Multi-surface Layer 4: `nutri-offline/scripts/mobile/semantic_surfaces.py`, `build_semantic_surfaces.py`
- Intent regex gate: `nutri-offline/scripts/mobile/intent_regex_gate.py`
- Latency benchmark: `nutri-offline/scripts/mobile/benchmark_semantic_v2.py`
- Household portions Layer 5: `nutri-offline/scripts/mobile/household_portions.py`
- BR-RET-002 grounding: `nutri-offline/scripts/dataset/answers.py` → `scale_nutrient()`
