# BR-005 — PR Only on Session Completion

| Property | Value |
|----------|-------|
| **Code** | `BR-005` |
| **Class** | `PersonalRecordEvaluationRule` |
| **Module** | `:domain` |

## Rule

```
GIVEN a workout session with logged sets
WHEN  the session transitions to Completed
THEN  personal records are evaluated against all sets in that session
AND   PersonalRecordAchieved events are raised for strictly improved metrics
AND   no PR evaluation occurs during InProgress or on Cancelled sessions
```

## Metrics Evaluated

| Metric | Comparison |
|--------|------------|
| `MAX_WEIGHT` | Highest weight across any set for the exercise |
| `MAX_REPS` | Highest reps at the session's max weight for the exercise |

## Use Cases

- [UC-005 Complete Workout Session](../use-cases/UC-005-complete-workout-session.md)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | Session InProgress, new max weight set | Log set | No PR update |
| 2 | Session completes, weight beats PR | Complete | `PersonalRecordAchieved` |
| 3 | Session cancelled | Cancel | No PR evaluation |
