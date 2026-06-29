# Phase 9 — Semantic nutrition engine (v2)

> **Status:** In progress (N-09-01–03 done) · **Parent:** [Phase 8](../08-mobile-pack/README.md)  
> **Goal:** Replace classic single-surface RAG as the primary mobile resolution path with a **five-layer semantic engine**: spell-fix → synonyms → ontology → multi-surface vectors → portion rules → deterministic SQLite lookup.

---

## Why Phase 9

Phase 8 ships a ≤200 MB mobile pack with desktop capability parity on clean inputs. Remaining failures (`arror`, `carne vermelha`, `uma manga inteira`, alias gaps) are **normalization and ontology** problems — not model size.

See [SEMANTIC-ENGINE-V2.md](../../docs/SEMANTIC-ENGINE-V2.md) for the full design.

---

## Architecture (target)

```
User question (PT-BR)
        │
        ▼
Intent parser (Phase 8 — extended)
        │
        ▼
Layer 1 — spell-fix (N-09-01) ✅
Layer 2 — synonyms (N-09-02) ✅
Layer 3 — ontology (N-09-03) ✅
Layer 4 — multi-surface vectors (N-09-04)
Layer 5 — household portions (N-09-05)
        │
        ▼
SemanticResolver pipeline (N-09-06)
        │
        ▼
SQLite ground truth → scale_nutrient → template answer
```

**Business rules:**

| ID | Rule |
|----|------|
| BR-NORM-001 | Spell correction only when edit distance ≤ 2 and candidate exists in lexicon |
| BR-NORM-002 | Colloquial phrase resolves via synonym map before vector search; default candidate when ambiguous |
| BR-NORM-003 | Category phrase resolves via ontology when synonyms miss; clarify note when multiple candidates |
| BR-PORT-001 | Household weights must cite source in debug metadata (Layer 5) |
| BR-RET-001/002 | Source boost + numeric grounding unchanged from Phase 8 |

---

## Exit criteria (Phase 9 complete)

- [x] `arror` → arroz 100g TACO kcal grounded
- [x] `carne vermelha` → patinho (default bovine cut) with TACO source
- [x] `pão francês` / `cacetinho` → same canonical bread row (TACO pão francês)
- [ ] `uma manga inteira` → kcal scaled to ~230g
- [ ] p95 latency ≤500 ms on mid-range CPU
- [ ] Pack still ≤200 MB (`schema_version` 2)

---

## Command sketch

```bash
cd nutri-offline && source venv/bin/activate

# Layer 1 — spell normalize (manual)
python scripts/mobile/spell_normalize.py "de arror"

# Layer 2 — synonym resolve (manual)
python scripts/mobile/build_synonyms.py
python scripts/mobile/synonym_resolver.py "cacetinho"

# Layer 3 — ontology resolve (manual)
python scripts/mobile/ontology_resolver.py "carne bovina"

# End-to-end mobile (layers 1–3 wired in mobile_search)
python scripts/app/nutri_cli.py ask "100g carne bovina" --runtime mobile

# Tests
python -m unittest tests.test_spell_normalize tests.test_synonym_resolver tests.test_ontology_resolver -v
./scripts/validate-nutri-mobile-pack.sh
```
