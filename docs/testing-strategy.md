# Testing Strategy

## Pyramid

```
        ┌─────────┐
        │  E2E    │  ~5%  — full flows (Compose UI Test)
        ├─────────┤
        │ Integr. │  ~20% — use cases + Room
        ├─────────┤
        │  Unit   │  ~75% — domain (base)
        └─────────┘
```

## Domain (`:domain`) — TDD Required

1. Write test **before** implementation
2. Format: **GIVEN / WHEN / THEN**
3. One assertion reason per test
4. No Android, no Room, no network
5. Coverage target: **≥ 90%** (JaCoCo)

### Test Locations

```
domain/src/test/kotlin/com/openfitness/domain/
├── model/
├── rule/
├── state/
└── valueobject/
```

## Application (`:application`)

- MockK for repository ports
- Turbine for `Flow` use cases
- Verify `AppError` mapping from domain exceptions

## Infrastructure (`:data`)

- Room in-memory database
- Migration tests with exported schema
- `BundledExerciseCatalogParser` fixtures with kxml2 (test only)
- MockWebServer for future network tests

## UI (`:app`)

- Compose UI Test for critical flows (start session → log set → complete)
- Screenshot/snapshot tests for design system components
- AndroidX Test Orchestrator for instrumented runs

## CI Targets

| Module | Gate |
|--------|------|
| `:domain` | Unit tests + JaCoCo ≥ 90% |
| `:application` | Unit tests pass |
| `:data` | Unit + migration tests pass |
| `:app` | Lint + selected UI tests |

## Reference

Business rule tests are specified in each [BR-xxx](../business-rules/README.md) document.
