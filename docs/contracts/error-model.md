# Contract — Error Model

Structured errors defined in `:application`, mapped to i18n in `:app`.

## AppError Hierarchy

```kotlin
sealed class AppError {
    data object ValidationError : AppError()
    data object NotFound : AppError()
    data object StorageError : AppError()
    data object ConflictError : AppError()       // e.g., session already in progress
    data class DuplicateExerciseName(val name: String) : AppError()
    data class InvalidStateTransition(val from: String, val to: String) : AppError()
}
```

## Domain → AppError Mapping

| Domain Exception | AppError |
|----------------|----------|
| `DuplicateExerciseNameException` | `DuplicateExerciseName` |
| `InvalidStateTransitionException` | `InvalidStateTransition` |
| `DomainException` (generic validation) | `ValidationError` |
| Room / IO failure | `StorageError` |
| Entity not found | `NotFound` |

## UI Mapping

```kotlin
// :app — ErrorMessageMapper
fun AppError.toMessage(resources: Resources): String
fun AppError.toRecoveryAction(): RecoveryAction?  // Retry, Dismiss, NavigateBack
```

## i18n Keys

| AppError | String key |
|----------|------------|
| `ValidationError` | `error_validation` |
| `NotFound` | `error_not_found` |
| `StorageError` | `error_storage` |
| `DuplicateExerciseName` | `error_duplicate_exercise_name` |
| `InvalidStateTransition` | `error_invalid_state` |
| `ConflictError` | `error_session_in_progress` |

## Rules

- Never show stack traces or exception class names
- Differentiate informational messages from failures (e.g., "already up to date" vs network error)
- Every error screen offers a recovery action when possible
