# Entity — WorkoutSession

| Property | Value |
|----------|-------|
| **Aggregate Root** | Yes |
| **Identity** | `SessionId` (UUID) |
| **Module** | `:domain` → `com.openfitness.domain.model.WorkoutSession` |

## Definition

A **WorkoutSession** is a single workout execution. It tracks lifecycle status, referenced exercises, and child set logs. Once `Completed`, the session and its set logs are **immutable** (BR-006).

## Attributes

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `SessionId` | yes | Domain-generated |
| `templateId` | `TemplateId?` | no | Source template if any |
| `status` | `SessionStatus` | yes | State machine controlled |
| `exercises` | `List<SessionExercise>` | yes | Min 1 when started |
| `setLogs` | `List<SetLog>` | yes | Grows during session |
| `startedAt` | `Instant?` | no | Set on `InProgress` |
| `completedAt` | `Instant?` | no | Set on `Completed` |
| `cancelledAt` | `Instant?` | no | Set on `Cancelled` |

### SessionExercise (child)

| Field | Type | Required |
|-------|------|----------|
| `exerciseId` | `ExerciseId` | yes |
| `order` | `Int` | yes |

## Invariants

1. Status transitions follow [Workout Session Lifecycle](../state-machines/workout-session-lifecycle.md).
2. `setLogs` can only be added while `status == IN_PROGRESS`.
3. Completed sessions cannot be modified (BR-006).
4. Must have ≥ 1 exercise to transition to `IN_PROGRESS` (BR-003).
5. `completedAt` is set only on `Completed`; `cancelledAt` only on `Cancelled`.

## Behavior

```kotlin
fun start(): WorkoutSession           // PLANNED → IN_PROGRESS, raises WorkoutSessionStarted
fun logSet(setLog: SetLog): WorkoutSession  // validates IN_PROGRESS, raises SetLogged
fun complete(): WorkoutSession        // IN_PROGRESS → COMPLETED, raises WorkoutSessionCompleted
fun cancel(): WorkoutSession          // IN_PROGRESS → CANCELLED
```

## State Machine

See [workout-session-lifecycle.md](../state-machines/workout-session-lifecycle.md).

## Relationships

| Related entity | Cardinality | Description |
|----------------|-------------|-------------|
| WorkoutTemplate | many-to-one | Optional source |
| SetLog | one-to-many | Owned children |
| PersonalRecord | indirect | PR evaluation on completion |

## Applied Business Rules

| Code | Rule |
|------|------|
| BR-003 | [Session must have exercises](../business-rules/BR-003-session-must-have-exercises.md) |
| BR-006 | [Immutable workout history](../business-rules/BR-006-immutable-workout-history.md) |

## Domain Events

| Event | When |
|-------|------|
| `WorkoutSessionStarted` | `start()` |
| `SetLogged` | `logSet()` |
| `WorkoutSessionCompleted` | `complete()` |

## Use Cases

- [UC-003 Start Workout Session](../use-cases/UC-003-start-workout-session.md)
- [UC-005 Complete Workout Session](../use-cases/UC-005-complete-workout-session.md)

## Tests Required

- Invalid transition throws `InvalidStateTransitionException`
- Set log rejected when not `IN_PROGRESS`
- Completed session rejects further mutations
- `WorkoutSessionStarted` event emitted on start
