# UC-009 — Edit Workout Template

| Property | Value |
|----------|-------|
| **Code** | `UC-009` |
| **Actor** | User |
| **Use Case** | `UpdateWorkoutTemplateUseCase` |

## Preconditions

- Template exists in local storage
- User on template list or detail screen

## Main Flow

1. User taps a template to edit.
2. User updates template name and/or exercise list.
3. System validates BR-003 (≥ 1 exercise when exercises are replaced).
4. System persists updated `WorkoutTemplate`.
5. UI refreshes template list.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| Template not found | `AppError.NotFound` |
| Blank name | `AppError.ValidationError` |
| Zero exercises after edit | `AppError.ValidationError` |

## Applied Rules

- BR-003

## Events Fired

None (v1).

## UI States

`loading` → `success` | `error`

## i18n Keys

- `edit_template_title`
- `template_name_label`
