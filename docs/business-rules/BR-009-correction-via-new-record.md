# BR-009 — Correction Via New Record

| Property | Value |
|----------|-------|
| **Code** | `BR-009` |
| **Class** | `RecordCorrection` model + append-only persistence |
| **Module** | `:domain` + `:data` |

## Rule

```
GIVEN a completed workout session and an existing set log
WHEN  the user corrects logged weight or reps
THEN  the system appends a RecordCorrection referencing the original set log
AND   the original set log row is never updated or deleted
```

## Applies To

- `RecordCorrection` aggregate
- `record_corrections` Room table (append-only)
- `CorrectCompletedSetUseCase`

## Infrastructure

- No `UPDATE`/`DELETE` DAO methods on `record_corrections`
- `SetLogRepository` blocks mutations when parent session is COMPLETED (BR-006)

## Use Cases

- [UC-011 Correct Completed Set](../use-cases/UC-011-correct-completed-set.md)
- [UC-006 View Workout History](../use-cases/UC-006-view-workout-history.md)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | COMPLETED session | append RecordCorrection | Passes |
| 2 | COMPLETED session | updateSetLog in-place | Fails (BR-006) |
| 3 | IN_PROGRESS session | CorrectCompletedSetUseCase | Fails |
