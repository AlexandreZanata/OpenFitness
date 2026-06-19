# UC-010 — Edit Custom Exercise

| Property | Value |
|----------|-------|
| **Code** | `UC-010` |
| **Actor** | User |
| **Use Case** | `UpdateCustomExerciseUseCase` |

## Preconditions

- Exercise exists with `isCustom = true`
- User on exercise library screen

## Main Flow

1. User taps a custom exercise.
2. System opens edit dialog.
3. User updates name, muscle group, and equipment.
4. System validates BR-001 (name uniqueness) and BR-007 (custom only).
5. System persists updated `Exercise`.
6. Library list refreshes.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| Bundled exercise | Not editable — no edit action shown |
| Duplicate name | `AppError.DuplicateExerciseName` |
| Exercise not found | `AppError.NotFound` |

## Applied Rules

- BR-001, BR-007

## Events Fired

None (v1).

## UI States

`success` | `error`

## i18n Keys

- `edit_exercise_title`
- `exercise_name_label`
