# Domain Event — SetLogged

| Property | Value |
|----------|-------|
| **Name** | `SetLogged` |
| **Aggregate** | `WorkoutSession` |
| **Raised by** | `WorkoutSession.logSet()` |

## Payload

| Field | Type |
|-------|------|
| `sessionId` | `SessionId` |
| `setLogId` | `SetLogId` |
| `exerciseId` | `ExerciseId` |
| `setNumber` | `Int` |
| `weightKg` | `Double?` |
| `reps` | `Int?` |
| `completedAt` | `Instant` |

## When

```
GIVEN a session in IN_PROGRESS
WHEN  a valid set is logged
THEN  SetLogged is raised
```

## Use Case

- [UC-004](../use-cases/UC-004-log-set.md)
