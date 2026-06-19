# Value Object — ExerciseId

| Type | `@JvmInline value class` wrapping `UUID` |
|------|------------------------------------------|
| **Module** | `com.openfitness.domain.valueobject.ExerciseId` |

## Invariants

- Must be a valid UUID v4
- Non-null, non-empty string representation

## Factory

```kotlin
@JvmInline
value class ExerciseId(val value: UUID) {
    companion object {
        fun generate(): ExerciseId = ExerciseId(UUID.randomUUID())
        fun fromString(raw: String): ExerciseId  // throws on invalid
    }
}
```

## Usage

- Entity identity for `Exercise`
- Foreign key reference in templates, sessions, set logs, PRs
