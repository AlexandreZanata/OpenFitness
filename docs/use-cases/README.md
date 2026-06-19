# Use Cases

Product flows documented before implementation. **Undocumented use cases must not be implemented.**

## Index

| Code | Name | Actor |
|------|------|-------|
| UC-001 | [Browse Exercise Library](UC-001-browse-exercise-library.md) | User |
| UC-002 | [Create Workout Template](UC-002-create-workout-template.md) | User |
| UC-003 | [Start Workout Session](UC-003-start-workout-session.md) | User |
| UC-004 | [Log Set](UC-004-log-set.md) | User |
| UC-005 | [Complete Workout Session](UC-005-complete-workout-session.md) | User |
| UC-006 | [View Workout History](UC-006-view-workout-history.md) | User |
| UC-007 | [View Personal Records](UC-007-view-personal-records.md) | User |

## Template

Each use case file contains: Actor, Preconditions, Main flow, Alternative flows, Applied rules, Events fired, UI states, Application class.

## Implementation Mapping

| Use Case | Application Class |
|----------|-------------------|
| UC-001 | `BrowseExercisesUseCase`, `CreateCustomExerciseUseCase` |
| UC-002 | `CreateWorkoutTemplateUseCase` |
| UC-003 | `StartWorkoutSessionUseCase` |
| UC-004 | `LogSetUseCase` |
| UC-005 | `CompleteWorkoutSessionUseCase` |
| UC-006 | `ViewWorkoutHistoryUseCase` |
| UC-007 | `ViewPersonalRecordsUseCase` |
