# UC-006 — View Workout History

| Property | Value |
|----------|-------|
| **Code** | `UC-006` |
| **Actor** | User |
| **Use Case** | `ViewWorkoutHistoryUseCase` |

## Preconditions

- None — empty history is valid

## Main Flow

1. User opens History screen.
2. System loads completed sessions ordered by `completedAt` descending.
3. System displays session cards: date, duration, exercise count, total sets.
4. User taps a session.
5. System shows read-only detail with all set logs.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| No completed sessions | Empty state with CTA to start workout |
| User attempts edit | Not available — BR-006 (immutable) |

## Applied Rules

- BR-006

## Events Fired

None (read-only).

## UI States

`loading` → `success` | `empty` | `error`

## Data Freshness

Show `history_last_workout` label with relative date from last `completedAt`.
