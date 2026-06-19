# Value Object — RepCount

| Type | `@JvmInline value class` wrapping `Int` |
|------|---------------------------------------|
| **Module** | `com.openfitness.domain.valueobject.RepCount` |

## Invariants

- Value must be **≥ 1** (BR-002)
- Integer only — no fractional reps

## Factory

```kotlin
@JvmInline
value class RepCount(val value: Int) {
    init {
        require(value >= 1) { "Rep count must be at least 1" }
    }
}
```

## Applied Rules

- [BR-002](../business-rules/BR-002-positive-set-values.md)
- [BR-004](../business-rules/BR-004-completed-set-requires-metrics.md)
