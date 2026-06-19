# UC-005 — Complete Workout Session

| Property | Value |
|----------|-------|
| **Code** | `UC-005` |
| **Actor** | User |
| **Use Case** | `CompleteWorkoutSessionUseCase` |

## Preconditions

- Session status is `IN_PROGRESS`
- At least zero sets logged (empty completion allowed — user may cancel instead)

## Main Flow

1. User taps "Finish Workout".
2. System shows confirmation dialog with summary (duration, total sets).
3. User confirms.
4. Session transitions to `COMPLETED`.
5. System emits `WorkoutSessionCompleted`.
6. System evaluates PRs per BR-005 across all sets.
7. For each improved metric, system emits `PersonalRecordAchieved` and persists.
8. System navigates to summary screen highlighting new PRs.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| User dismisses dialog | No state change |
| Session already completed | BR-006 blocks |
| Zero sets logged | Allow completion — empty workout recorded |

## Applied Rules

- BR-005, BR-006

## Events Fired

- `WorkoutSessionCompleted`
- `PersonalRecordAchieved` (0..n)

## UI States

`loading` during PR evaluation → `success` with PR badges
