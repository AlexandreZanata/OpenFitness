# BR-006 — Immutable Workout History

| Property | Value |
|----------|-------|
| **Code** | `BR-006` |
| **Class** | Enforced on `WorkoutSession`, repositories |
| **Module** | `:domain` + `:data` |

## Rule

```
GIVEN a workout session in Completed status
WHEN  any mutation is attempted on the session or its set logs
THEN  the operation is rejected with DomainException
AND   corrections are made only by creating new records that reference the original
```

## Applies To

- `WorkoutSession` aggregate after `Completed`
- Child `SetLog` entries of completed sessions
- `PersonalRecord` history entries (append-only)

## Infrastructure

- Room DAOs expose no `UPDATE`/`DELETE` for completed session tables
- Repository implementations guard at domain level first

## Use Cases

- All session write use cases
- [UC-006 View Workout History](../use-cases/UC-006-view-workout-history.md)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | Completed session | logSet() | Fails |
| 2 | Completed session | cancel() | Fails |
| 3 | InProgress session | logSet() | Passes |
