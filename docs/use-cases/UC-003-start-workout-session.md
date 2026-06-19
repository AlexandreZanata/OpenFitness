# UC-003 — Start Workout Session

| Property | Value |
|----------|-------|
| **Code** | `UC-003` |
| **Actor** | User |
| **Use Case** | `StartWorkoutSessionUseCase` |

## Preconditions

- A workout template exists **or** user builds ad-hoc exercise list
- No other session in `IN_PROGRESS` (v1: single active session)

## Main Flow

1. User selects template or creates ad-hoc session.
2. System creates `WorkoutSession` in `PLANNED` with exercises.
3. User taps "Start Workout".
4. System validates BR-003.
5. Session transitions to `IN_PROGRESS` via state machine.
6. System emits `WorkoutSessionStarted`.
7. System navigates to Active Session screen.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| Empty exercise list | Block start, show validation |
| Session already in progress | Show dialog — resume or cancel existing |
| Invalid transition | `AppError.ValidationError` |

## Applied Rules

- BR-003

## Events Fired

- `WorkoutSessionStarted`

## UI States

Active Session: `loading` → `success` with rest timer ready
