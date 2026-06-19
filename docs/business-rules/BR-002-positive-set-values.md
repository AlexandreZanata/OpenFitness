# BR-002 — Positive Set Values

| Property | Value |
|----------|-------|
| **Code** | `BR-002` |
| **Class** | `PositiveSetValuesRule` |
| **Module** | `:domain` |

## Rule

```
GIVEN a set being logged
WHEN  weight and/or reps are provided
THEN  weight must be > 0 kg if present
AND   reps must be ≥ 1 if present
AND   DomainException is thrown for zero or negative values
```

## Implementation

Enforced by `Weight` and `RepCount` value object constructors and `PositiveSetValuesRule.validate()`.

## Use Cases

- [UC-004 Log Set](../use-cases/UC-004-log-set.md)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | — | Weight = 0 kg | Fails |
| 2 | — | Weight = 60 kg, Reps = 8 | Passes |
| 3 | — | Reps = 0 | Fails |
