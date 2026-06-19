# Domain Event — WorkoutSessionStarted

| Property | Value |
|----------|-------|
| **Name** | `WorkoutSessionStarted` |
| **Aggregate** | `WorkoutSession` |
| **Raised by** | `WorkoutSession.start()` |

## Payload

| Field | Type |
|-------|------|
| `sessionId` | `SessionId` |
| `templateId` | `TemplateId?` |
| `exerciseIds` | `List<ExerciseId>` |
| `startedAt` | `Instant` |

## When

```
GIVEN a session in PLANNED status with ≥ 1 exercise
WHEN  start() is called
THEN  WorkoutSessionStarted is raised
```

## Consumers (v1)

- Use case logging / future analytics hook (disabled v1)

## Use Case

- [UC-003](../use-cases/UC-003-start-workout-session.md)
