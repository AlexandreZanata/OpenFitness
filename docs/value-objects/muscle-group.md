# Value Object — MuscleGroup

| Type | `enum class` |
|------|--------------|
| **Module** | `com.openfitness.domain.valueobject.MuscleGroup` |

## Values

See [Glossary — MuscleGroup](../glossary.md#musclegroup).

```kotlin
enum class MuscleGroup {
    CHEST, BACK, SHOULDERS, BICEPS, TRICEPS,
    LEGS, CORE, FULL_BODY, CARDIO,
}
```

## Invariants

- Must be a defined enum constant — no free-text muscle names in domain
- External/bundled data normalized to enum at infrastructure boundary

## i18n

- Enum name is **not** shown to users
- UI maps each value to a string resource key: `muscle_group_chest`, etc.
