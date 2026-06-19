# BR-003 — Session Must Have Exercises

| Property | Value |
|----------|-------|
| **Code** | `BR-003` |
| **Class** | `SessionMustHaveExercisesRule` |
| **Module** | `:domain` |

## Rule

```
GIVEN a workout template or session
WHEN  it is saved or started
THEN  it must contain at least one exercise
AND   DomainException is thrown if the exercise list is empty
```

## Applies To

- `WorkoutTemplate` creation/update
- `WorkoutSession.start()` transition

## Use Cases

- [UC-002 Create Workout Template](../use-cases/UC-002-create-workout-template.md)
- [UC-003 Start Workout Session](../use-cases/UC-003-start-workout-session.md)

## Tests

| # | GIVEN | WHEN | THEN |
|---|-------|------|------|
| 1 | Template with 0 exercises | Save | Fails |
| 2 | Session with 0 exercises | Start | Fails |
| 3 | Session with 1 exercise | Start | Passes |
