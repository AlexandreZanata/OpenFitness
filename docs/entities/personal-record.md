# Entity — PersonalRecord

| Property | Value |
|----------|-------|
| **Aggregate Root** | Yes |
| **Identity** | Composite: `ExerciseId` + `PersonalRecordMetric` |
| **Module** | `:domain` → `com.openfitness.domain.model.PersonalRecord` |

## Definition

A **PersonalRecord (PR)** tracks the user's best performance for an exercise on a specific metric. PRs are evaluated and updated **only when a workout session completes** (BR-005).

## Attributes

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `exerciseId` | `ExerciseId` | yes | |
| `metric` | `PersonalRecordMetric` | yes | `MAX_WEIGHT` or `MAX_REPS` |
| `value` | `Double` | yes | kg for weight, count for reps |
| `achievedAt` | `Instant` | yes | Session completion time |
| `sessionId` | `SessionId` | yes | Source session reference |
| `setLogId` | `SetLogId` | yes | Source set reference |

## Invariants

1. `value` > 0.
2. Updated only via `tryUpdate(candidate)` during session completion — never mid-session.
3. New value must strictly exceed previous value to replace (equal does not update).
4. History of superseded PRs is preserved as new records (BR-006 pattern).

## Behavior

```kotlin
fun tryUpdate(candidate: PersonalRecordCandidate): PersonalRecordUpdateResult
// Returns: NoChange | NewRecord(event: PersonalRecordAchieved)
```

## Applied Business Rules

| Code | Rule |
|------|------|
| BR-005 | [PR only on session completion](../business-rules/BR-005-pr-only-on-session-completion.md) |
| BR-006 | [Immutable workout history](../business-rules/BR-006-immutable-workout-history.md) |

## Domain Events

| Event | When |
|-------|------|
| `PersonalRecordAchieved` | New PR strictly beats previous |

## Use Cases

- [UC-005 Complete Workout Session](../use-cases/UC-005-complete-workout-session.md) (PR evaluation)
- [UC-007 View Personal Records](../use-cases/UC-007-view-personal-records.md)

## Tests Required

- Mid-session set does not update PR
- Equal value does not trigger `PersonalRecordAchieved`
- Higher weight triggers event and replaces record
- Superseded record remains in history table
