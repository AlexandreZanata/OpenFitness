# Domain Event — SetLogUpdated

| Property | Value |
|----------|-------|
| **Name** | `SetLogUpdated` |
| **Aggregate** | `WorkoutSession` |
| **Raised by** | `WorkoutSession.updateSetLog()` |

## Payload

| Field | Type |
|-------|------|
| `sessionId` | `SessionId` |
| `setLogId` | `SetLogId` |
| `weightKg` | `Double?` |
| `reps` | `Int?` |

## When

```
GIVEN a session in IN_PROGRESS
WHEN  an existing set log is updated with valid metrics
THEN  SetLogUpdated is raised
```

```
GIVEN a session in COMPLETED
WHEN  updateSetLog is called
THEN  fails — BR-008 (SetEditableInProgressOnlyRule)
```

## Use Case

- [UC-008](../use-cases/UC-008-edit-set-during-session.md)
