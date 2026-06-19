# BR-004 — Completed Set Requires Metrics

| Property | Value |
|----------|-------|
| **Code** | `BR-004` |
| **Class** | `CompletedSetRequiresMetricsRule` |
| **Module** | `:domain` |

## Rule

```
GIVEN a set marked as completed
WHEN  the set log is created
THEN  at least one of weight or reps must be present
AND   DomainException is thrown if both are absent
```

## Rationale

A completed set must record measurable performance. Cardio sets may use reps-only; weighted lifts use both.

## Use Cases

- [UC-004 Log Set](../use-cases/UC-004-log-set.md)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | weight=null, reps=null | Create set | Fails |
| 2 | weight=50kg, reps=null | Create set | Passes |
| 3 | weight=null, reps=12 | Create set | Passes |
