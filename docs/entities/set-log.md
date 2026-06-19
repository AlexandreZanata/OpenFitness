# Entity — SetLog

| Property | Value |
|----------|-------|
| **Aggregate Root** | No — child of `WorkoutSession` |
| **Identity** | `SetLogId` (UUID) |
| **Module** | `:domain` → `com.openfitness.domain.model.SetLog` |

## Definition

A **SetLog** records one performed set: which exercise, weight, reps, and when it was completed. Set logs belong to a `WorkoutSession` and become immutable when the parent session completes.

## Attributes

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `SetLogId` | yes | Domain-generated |
| `sessionId` | `SessionId` | yes | Parent reference |
| `exerciseId` | `ExerciseId` | yes | |
| `setNumber` | `Int` | yes | 1-based within exercise |
| `weight` | `Weight` | conditional | Required for weighted exercises (BR-004) |
| `reps` | `RepCount` | conditional | Required for rep-based exercises (BR-004) |
| `completedAt` | `Instant` | yes | |

## Invariants

1. `setNumber` ≥ 1.
2. Weight and reps must be positive when present (BR-002).
3. At least one of weight or reps must be present (BR-004).
4. `exerciseId` must exist in parent session's exercise list.
5. Immutable after parent session reaches `Completed`.

## Behavior

```kotlin
companion object {
    fun create(
        sessionId: SessionId,
        exerciseId: ExerciseId,
        setNumber: Int,
        weight: Weight?,
        reps: RepCount?,
    ): SetLog
}
```

Validation runs in `create()` — invalid sets never exist as objects.

## Applied Business Rules

| Code | Rule |
|------|------|
| BR-002 | [Positive set values](../business-rules/BR-002-positive-set-values.md) |
| BR-004 | [Completed set requires metrics](../business-rules/BR-004-completed-set-requires-metrics.md) |

## Domain Events

| Event | When |
|-------|------|
| `SetLogged` | Raised by parent `WorkoutSession.logSet()` |

## Use Cases

- [UC-004 Log Set](../use-cases/UC-004-log-set.md)

## Tests Required

- Zero reps and zero weight fails
- Negative weight fails
- Zero reps fails
- Valid weighted set is created
