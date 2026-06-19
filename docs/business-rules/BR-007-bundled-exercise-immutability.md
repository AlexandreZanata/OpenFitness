# BR-007 — Bundled Exercise Immutability

| Property | Value |
|----------|-------|
| **Code** | `BR-007` |
| **Class** | `BundledExerciseImmutabilityRule` |
| **Module** | `:domain` |

## Rule

```
GIVEN an exercise where isCustom = false
WHEN  a rename, muscle group change, or delete is attempted
THEN  the operation is rejected with DomainException
AND   bundled catalog integrity is preserved across app versions
```

## Rationale

Bundled exercises ship with the app assets. Users customize via custom exercises, not by mutating seed data.

## Use Cases

- [UC-001 Browse Exercise Library](../use-cases/UC-001-browse-exercise-library.md)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | Bundled "Squat" | Rename | Fails |
| 2 | Custom "My Squat" | Rename | Passes |
| 3 | Bundled exercise | Delete | Fails |
