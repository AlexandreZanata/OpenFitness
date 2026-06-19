# Value Object — Weight

| Type | `@JvmInline value class` wrapping `Double` (kilograms) |
|------|--------------------------------------------------------|
| **Module** | `com.openfitness.domain.valueobject.Weight` |

## Invariants

- Value must be **> 0** (BR-002)
- Stored internally in **kilograms** — UI converts for display locale
- Rounded to 2 decimal places on creation

## Factory

```kotlin
@JvmInline
value class Weight(val kilograms: Double) {
    init {
        require(kilograms > 0) { "Weight must be positive" }
    }
    companion object {
        fun fromKilograms(kg: Double): Weight
    }
}
```

## Display

- UI uses `Locale`-aware formatting via string resources
- Logs mask nothing (local-only app, no PII in weight)

## Applied Rules

- [BR-002](../business-rules/BR-002-positive-set-values.md)
