# Contract — UI State

ViewModel pattern for all feature screens.

## Pattern

```kotlin
data class FeatureUiState(
    val isLoading: Boolean = false,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
    // feature-specific success payload fields
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

### ExerciseLibraryUiState (UC-001, UC-010)

```kotlin
data class ExerciseLibraryUiState(
    val exercises: List<ExerciseUiModel> = emptyList(),
    val searchQuery: String = "",
    val selectedFilter: MuscleGroup? = null,
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
    val showAddDialog: Boolean = false,
    val showEditDialog: Boolean = false,       // UC-010
    val editingExerciseId: ExerciseId? = null, // UC-010
)
```

### TemplatesUiState (UC-002, UC-009)

```kotlin
data class TemplatesUiState(
    val templates: List<TemplateUiModel> = emptyList(),
    val availableExercises: List<Pair<ExerciseId, String>> = emptyList(),
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
    val showCreateDialog: Boolean = false,
    val showEditDialog: Boolean = false,       // UC-009
    val editingTemplateId: TemplateId? = null, // UC-009
)
```

### ActiveSessionUiState (UC-003–005, UC-008)

```kotlin
data class ActiveSessionUiState(
    val sessionId: String? = null,
    val exercises: List<SessionExerciseUiModel> = emptyList(),
    val currentExerciseIndex: Int = 0,
    val setLogs: List<SetLogUiModel> = emptyList(),
    val weightInput: String = "",
    val repsInput: String = "",
    val restTimerSecondsRemaining: Int? = null,
    val isLoading: Boolean = true,
    val error: AppError? = null,
    val showFinishDialog: Boolean = false,
    val showEditSetDialog: Boolean = false,    // UC-008
    val editingSetLogId: SetLogId? = null,     // UC-008
    val isCompleted: Boolean = false,
    val newPrCount: Int = 0,
)
```

### HistoryUiState (UC-006, UC-011)

```kotlin
data class HistoryUiState(
    val sessions: List<HistorySessionUiModel> = emptyList(),
    val lastWorkoutLabel: String? = null,
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
    val selectedSessionId: SessionId? = null,
    val selectedSessionDetail: HistorySessionDetailUiModel? = null,
    val isLoadingDetail: Boolean = false,
    val showCorrectDialog: Boolean = false,    // UC-011
    val correctingSetLogId: SetLogId? = null,  // UC-011
)
```

### PersonalRecordsUiState (UC-007)

```kotlin
data class PersonalRecordsUiState(
    val records: List<PersonalRecordUiModel> = emptyList(),
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
