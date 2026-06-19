# Domain Event — WorkoutSessionCompleted

| Property | Value |
|----------|-------|
| **Name** | `WorkoutSessionCompleted` |
| **Aggregate** | `WorkoutSession` |
| **Raised by** | `WorkoutSession.complete()` |

## Payload

| Field | Type |
|-------|------|
| `sessionId` | `SessionId` |
| `completedAt` | `Instant` |
| `totalSets` | `Int` |
| `durationSeconds` | `Long` |

## When

```
GIVEN a session in IN_PROGRESS
WHEN  complete() is called
THEN  WorkoutSessionCompleted is raised
AND   PR evaluation runs (may emit PersonalRecordAchieved)
```

## Use Case

- [UC-005](../use-cases/UC-005-complete-workout-session.md)
