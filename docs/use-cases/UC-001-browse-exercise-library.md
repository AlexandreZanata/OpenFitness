# UC-001 — Browse Exercise Library

| Property | Value |
|----------|-------|
| **Code** | `UC-001` |
| **Actor** | User |
| **Use Cases** | `BrowseExercisesUseCase`, `CreateCustomExerciseUseCase` |

## Preconditions

- App launched; bundled catalog seeded on first run (infrastructure)
- Local Room database available

## Main Flow — Browse

1. User opens Exercise Library screen.
2. System loads exercises from local repository (FTS-backed search).
3. User enters search query (optional).
4. System filters exercises by name and muscle group.
5. System displays list with name, muscle group, equipment icon.

## Alternative Flow — Create Custom Exercise

1. User taps "Add Exercise".
2. User enters name, muscle group, equipment.
3. System validates BR-001 (name uniqueness).
4. System creates `Exercise` with `isCustom = true`.
5. System persists and refreshes list.

## Alternative Flows — Errors

| Condition | Behavior |
|-----------|----------|
| Duplicate name | Show `AppError.ValidationError` with i18n message |
| Empty search results | Show empty state — not an error |
| DB unavailable | Show `AppError.StorageError` with retry |

## Applied Rules

- BR-001, BR-007

## Events Fired

None (v1).

## UI States

`loading` → `success` | `empty` | `error`

## i18n Keys

- `exercise_library_title`
- `exercise_library_empty`
- `exercise_library_add`
- `error_duplicate_exercise_name`
