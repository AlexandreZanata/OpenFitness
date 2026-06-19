# UC-004 — Log Set

| Property | Value |
|----------|-------|
| **Code** | `UC-004` |
| **Actor** | User |
| **Use Case** | `LogSetUseCase` |

## Preconditions

- Session status is `IN_PROGRESS`
- Exercise is part of current session

## Main Flow

1. User selects current exercise in active session.
2. User enters weight (kg) and/or reps.
3. User taps "Complete Set".
4. System validates BR-002, BR-004.
5. System creates `SetLog` and attaches to session aggregate.
6. System persists set log in transaction.
7. System emits `SetLogged`.
8. Rest timer starts (UI — DataStore preference for duration).
9. UI updates set counter for exercise.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| Session not InProgress | `AppError.ValidationError` |
| Invalid weight/reps | Inline field validation |
| Completed session | BR-006 blocks — `AppError.ValidationError` |

## Applied Rules

- BR-002, BR-004, BR-006

## Events Fired

- `SetLogged`

## UI States

Inline validation on fields; screen remains `success`
