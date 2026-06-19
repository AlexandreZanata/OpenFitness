# BR-001 — Exercise Name Uniqueness

| Property | Value |
|----------|-------|
| **Code** | `BR-001` |
| **Class** | `ExerciseNameUniquenessRule` |
| **Module** | `:domain` |

## Rule

```
GIVEN the local exercise library
WHEN  a user creates a custom exercise with name N
THEN  N is accepted only if no existing custom exercise has the same name (case-insensitive, trimmed)
AND   a DuplicateExerciseNameException is thrown otherwise
```

## Scope

- Applies to **custom exercises only**
- Bundled exercises are seeded once — uniqueness checked at seed time offline

## Implementation

```kotlin
class ExerciseNameUniquenessRule {
    fun validate(name: String, existingNames: List<String>)
}
```

Called by `CreateCustomExerciseUseCase` before `Exercise.createCustom()`.

## Use Cases

- [UC-001 Browse / Create Exercise](../use-cases/UC-001-browse-exercise-library.md)

## Tests (TDD)

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | No exercise named "curl" | Create "Curl" | Accepted |
| 2 | Custom exercise "Curl" exists | Create "curl" | `DuplicateExerciseNameException` |
| 3 | Bundled "Bench Press" exists | Create custom "bench press" | `DuplicateExerciseNameException` |
