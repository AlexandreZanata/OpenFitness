# UC-002 — Create Workout Template

| Property | Value |
|----------|-------|
| **Code** | `UC-002` |
| **Actor** | User |
| **Use Case** | `CreateWorkoutTemplateUseCase` |

## Preconditions

- At least one exercise exists in library
- User on Templates screen

## Main Flow

1. User taps "New Template".
2. User enters template name.
3. User adds exercises from library with target set counts.
4. User reorders exercises (optional).
5. System validates BR-003 (≥ 1 exercise).
6. System persists `WorkoutTemplate`.
7. System navigates to template detail.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| Zero exercises added | Block save, show validation message |
| Duplicate exercise in template | Block add, show inline error |
| Blank template name | Block save |

## Applied Rules

- BR-003

## Events Fired

None (v1).

## UI States

`loading` → `success` | `error`
