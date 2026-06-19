# Domain Events

Immutable facts that **already happened**. Names are always past tense.

## Index

| Event | Aggregate | Document |
|-------|-----------|----------|
| `WorkoutSessionStarted` | WorkoutSession | [workout-session-started.md](workout-session-started.md) |
| `SetLogged` | WorkoutSession | [set-logged.md](set-logged.md) |
| `WorkoutSessionCompleted` | WorkoutSession | [workout-session-completed.md](workout-session-completed.md) |
| `PersonalRecordAchieved` | PersonalRecord | [personal-record-achieved.md](personal-record-achieved.md) |

## Event Envelope

Every event carries:

| Field | Type | Description |
|-------|------|-------------|
| `eventId` | UUID | Unique event identifier |
| `occurredAt` | `Instant` | Timestamp |
| `aggregateId` | String | Root aggregate ID |
| `payload` | typed | Event-specific data |

Events are never edited or deleted.
