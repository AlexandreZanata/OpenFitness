# Official reference — Nutrition data sources

> Every download script must cite these URLs. Community mirrors are fallback only.

---

## TACO — Brazilian Table of Food Composition (NEPA/UNICAMP)

| Field | Value |
|-------|-------|
| **Authority** | NEPA — Núcleo de Estudos e Pesquisas em Alimentação, UNICAMP |
| **Homepage** | https://www.nepa.unicamp.br/taco/index.php |
| **4th edition** | https://nepa.unicamp.br/tabela-brasileira-de-composicao-de-alimentos-4a-edicao/ |
| **Official Excel** | https://nepa.unicamp.br/publicacoes/tabela-taco-excel/ |
| **Community CSV** | https://github.com/machine-learning-mocha/taco (derived — cite NEPA as primary) |
| **Coverage** | ~600 Brazilian foods, lab-analyzed |
| **License** | Public academic research data — always cite NEPA/UNICAMP |
| **Language** | Portuguese |

---

## TBCA — Brazilian Table of Food Composition (USP)

| Field | Value |
|-------|-------|
| **Authority** | USP — Universidade de São Paulo |
| **Portal** | https://www.tbca.net.br/ |
| **Coverage** | Complementary to TACO; biodiversity foods, dietary intake data |
| **License** | Academic — cite USP |
| **Priority** | P1 complement — use where TACO lacks coverage |
| **Phase 1 status** | No bulk export/API — deferred; notes in `data/raw/tbca/access-notes.json` |
| **Language** | Portuguese |

---

## FoodData Central — USDA

| Field | Value |
|-------|-------|
| **Authority** | USDA Agricultural Research Service |
| **Portal** | https://fdc.nal.usda.gov/ |
| **API key signup** | https://fdc.nal.usda.gov/api-key-signup/ |
| **API guide** | https://fdc.nal.usda.gov/api-guide/ |
| **Bulk downloads** | https://fdc.nal.usda.gov/download-datasets/ |
| **Coverage** | ~400k records — Foundation Foods (~8k gold standard) + Branded (~380k label data) |
| **License** | CC0 1.0 Universal — free use, cite USDA |
| **Rate limit** | API: 1,000 req/hour with key — prefer bulk for offline pipeline |
| **Language** | English |

### Recommended bulk files

| Dataset | Use |
|---------|-----|
| Foundation Foods | Generic foods with complete nutrient profile |
| Branded Foods | Commercial products with label data |
| Food Category | Category metadata for filtering |

---

## Open Food Facts

| Field | Value |
|-------|-------|
| **Portal** | https://world.openfoodfacts.org/data |
| **CSV dump** | https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz (~0.9 GB compressed) |
| **JSONL dump** | https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz (~7 GB compressed) |
| **Parquet** | Available on same data page — **recommended for DuckDB** |
| **Hugging Face** | https://huggingface.co/datasets/openfoodfacts/product-database |
| **Coverage** | ~3.7M global products — names, brands, ingredients, Nutri-Score |
| **License** | Open Database License (ODbL) — free use with attribution |
| **Processing tip** | Use DuckDB to query Parquet without loading full file into RAM |

---

## Attribution requirements (runtime + docs)

| Source | Required citation |
|--------|-------------------|
| TACO | "Tabela Brasileira de Composição de Alimentos, NEPA/UNICAMP" |
| TBCA | "TBCA, USP" |
| FDC | "USDA FoodData Central" |
| OFF | "Open Food Facts contributors" + ODbL notice |

Store `source` field on every normalized record: `taco` | `tbca` | `fdc` | `off`.

---

## Golden validation rows (post-normalization)

Use these in Phase 2 to verify parsing:

| Food | Source | Expected (per 100g) | Field |
|------|--------|---------------------|-------|
| Arroz, branco, cozido | TACO | ~128 kcal | energy_kcal |
| Arroz, branco, cozido | TACO | ~28g carbs | carbohydrate_g |
| Banana, prata, crua | TACO | verify against official table | energy_kcal |

Exact values must match official TACO 4th edition — do not hardcode from LLM memory.
