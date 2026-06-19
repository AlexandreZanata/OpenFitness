# State Machine — Workout Session Lifecycle

| Entity | `WorkoutSession` |
|--------|------------------|
| **Class** | `WorkoutSessionStateMachine` |
| **Module** | `:domain` |

## States

| State | Terminal | Description |
|-------|----------|-------------|
| `PLANNED` | no | Session created, not yet started |
| `IN_PROGRESS` | no | User is actively logging sets |
| `COMPLETED` | **yes** | Workout finished; history locked |
| `CANCELLED` | **yes** | Abandoned; no PR evaluation |

## Transitions

| From | To | Trigger | Actor | Side Effects |
|------|-----|---------|-------|--------------|
| `PLANNED` | `IN_PROGRESS` | `start()` | User | Set `startedAt`, emit `WorkoutSessionStarted` |
| `IN_PROGRESS` | `COMPLETED` | `complete()` | User | Set `completedAt`, emit `WorkoutSessionCompleted`, evaluate PRs |
| `IN_PROGRESS` | `CANCELLED` | `cancel()` | User | Set `cancelledAt` |
| `PLANNED` | `CANCELLED` | `cancel()` | User | Set `cancelledAt` |

## Invalid Transitions

All other combinations throw `InvalidStateTransitionException`:

- `COMPLETED` → any
- `CANCELLED` → any
- `PLANNED` → `COMPLETED` (must go through `IN_PROGRESS`)
- `IN_PROGRESS` → `PLANNED`

## Diagram

```
        ┌─────────┐
        │ PLANNED │
        └────┬────┘
             │ start()
             ▼
      ┌─────────────┐     cancel()     ┌───────────┐
      │ IN_PROGRESS │ ───────────────► │ CANCELLED │
      └──────┬──────┘                  └───────────┘
             │ complete()
             ▼
      ┌─────────────┐
      │  COMPLETED  │  (terminal)
      └─────────────┘
```

## Applied Rules

- BR-003 (exercises required to start)
- BR-005 (PR on complete only)
- BR-006 (immutable after complete)

## Tests

- Each valid transition succeeds
- Each invalid transition throws
- Terminal states reject all triggers
