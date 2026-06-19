# BR-008 — Set Editable In Progress Only

| Property | Value |
|----------|-------|
| **Code** | `BR-008` |
| **Class** | `SetEditableInProgressOnlyRule` |
| **Module** | `:domain` |

## Rule

```
GIVEN a workout session
WHEN  a set log update is attempted
THEN  the operation is allowed only if session status is IN_PROGRESS
AND   completed or cancelled sessions reject the mutation
```

## Applies To

- `WorkoutSession.updateSetLog()`
- Active session edit flows (UC-008)

## Infrastructure

- Repository guards still enforce BR-006 at persistence boundary
- Application layer maps `ImmutableRecordException` → `AppError.ValidationError`

## Use Cases

- [UC-008 Edit Set During Session](../use-cases/UC-008-edit-set-during-session.md)
- [UC-004 Log Set](../use-cases/UC-004-log-set.md) (related write path)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | IN_PROGRESS session | updateSetLog() | Passes |
| 2 | COMPLETED session | updateSetLog() | Fails |
| 3 | PLANNED session | updateSetLog() | Fails |
