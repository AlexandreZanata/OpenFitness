# Contract — UI State

ViewModel pattern for all feature screens.

## Pattern

```kotlin
data class FeatureUiState(
    val isLoading: Boolean = false,
    val content: ContentType? = null,      // success payload
    val isEmpty: Boolean = false,
    val error: AppError? = null,
)

sealed interface FeatureEvent {
    // user actions
}
```

## Required States per Screen

Every screen must handle:

| State | UI behavior |
|-------|-------------|
| `loading` | Skeleton or progress indicator |
| `empty` | Illustration + CTA (not an error) |
| `error` | Message from `ErrorMessageMapper` + recovery action |
| `success` | Primary content |

## Feature Contracts

### ExerciseLibraryUiState

```kotlin
data class ExerciseLibraryUiState(
    val exercises: List<ExerciseUiModel> = emptyList(),
    val searchQuery: String = "",
    val selectedFilter: MuscleGroup? = null,
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
)
```

### ActiveSessionUiState

```kotlin
data class ActiveSessionUiState(
    val sessionId: String?,
    val exercises: List<SessionExerciseUiModel> = emptyList(),
    val currentExerciseIndex: Int = 0,
    val completedSets: Map<String, Int> = emptyMap(),
    val restTimerSecondsRemaining: Int? = null,
    val isLoading: Boolean = false,
    val error: AppError? = null,
)
```

### HistoryUiState

```kotlin
data class HistoryUiState(
    val sessions: List<HistorySessionUiModel> = emptyList(),
    val lastWorkoutLabel: String? = null,
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
)
```

## Composable Contract

Screens are **stateless**:

```kotlin
@Composable
fun ActiveSessionScreen(
    state: ActiveSessionUiState,
    onEvent: (ActiveSessionEvent) -> Unit,
)
```

Enables `@Preview` and UI tests without ViewModel.

## ViewModel Rules

- Injects use cases only
- Exposes `StateFlow<FeatureUiState>`
- Maps domain → `UiModel` in ViewModel or dedicated mapper
- No `Context`, no DAOs, no business validation
