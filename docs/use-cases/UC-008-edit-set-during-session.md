# UC-008 — Edit Set During Session

| Property | Value |
|----------|-------|
| **Code** | `UC-008` |
| **Actor** | User |
| **Use Case** | `EditSetUseCase` |

## Preconditions

- Session status is `IN_PROGRESS`
- Set log exists in current session

## Main Flow

1. User taps a logged set in the active session screen.
2. System opens edit dialog with current weight and reps.
3. User updates values and saves.
4. System validates BR-002, BR-008.
5. `WorkoutSession.updateSetLog()` mutates the in-memory aggregate.
6. System persists session in a transaction.
7. System emits `SetLogUpdated`.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| Session not IN_PROGRESS | `AppError.ValidationError` |
| Set not found | `AppError.NotFound` |
| Invalid weight/reps | `AppError.ValidationError` |

## Applied Rules

- BR-002, BR-008

## Events Fired

- `SetLogUpdated`

## UI States

`success` with updated set list; inline error on validation failure

## i18n Keys

- `edit_set_title`
- `active_session_weight`
- `active_session_reps`
