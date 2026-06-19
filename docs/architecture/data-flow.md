# Data Flow

How data moves through layers for reads (queries) and writes (commands).

## Read Flow (Query)

```
Composable
    │  observes StateFlow
    ▼
ViewModel
    │  calls use case
    ▼
Use Case
    │  calls repository port
    ▼
Repository (interface — Domain)
    │  implemented by
    ▼
Repository Impl (:data)
    │  Room DAO / FTS query
    ▼
Mapper (entity → domain)
    ▼
Domain model
    │  mapped to
    ▼
UiModel (in :app mapper)
    ▼
UiState → Composable renders
```

### Example: Browse Exercise Library

1. `ExerciseLibraryScreen` collects `ExerciseLibraryUiState` from ViewModel.
2. `ExerciseLibraryViewModel` calls `BrowseExercisesUseCase(query)`.
3. Use case calls `ExerciseRepository.search(query)`.
4. `ExerciseRepositoryImpl` queries Room FTS on `exercises_fts`.
5. Mapper converts `ExerciseEntity` → `Exercise` domain model.
6. ViewModel maps `Exercise` → `ExerciseUiModel`, updates `UiState`.

---

## Write Flow (Command)

```
Composable
    │  onEvent(LogSet(...))
    ▼
ViewModel
    │  calls use case
    ▼
Use Case
    │  loads aggregate, applies rules
    ▼
Domain (entity / state machine / rules)
    │  on success, persist + events
    ▼
Repository (interface)
    ▼
Repository Impl
    │  transaction: insert/update
    ▼
Mapper (domain → entity)
    ▼
Room commit
    │
    ▼
Domain events collected by use case (for side effects / PR check)
```

### Example: Log Set

1. User taps "Complete Set" → `ActiveSessionEvent.CompleteSet`.
2. ViewModel calls `LogSetUseCase(sessionId, exerciseId, weight, reps)`.
3. Use case loads `WorkoutSession` aggregate from `WorkoutSessionRepository`.
4. Domain applies `PositiveSetValuesRule` (BR-002) and `CompletedSetRequiresMetricsRule` (BR-004).
5. Session state machine validates session is `InProgress`.
6. `SetLog` created; `SetLogged` event raised on aggregate.
7. `SetLogRepository.save(setLog)` persists within transaction.
8. Use case checks PR eligibility → may raise `PersonalRecordAchieved`.
9. ViewModel refreshes `UiState` or surfaces `AppError`.

---

## ViewModel Contract

ViewModels **orchestrate UI state** — they do not contain business logic.

```kotlin
data class ActiveSessionUiState(
    val session: SessionUiModel?,
    val exercises: List<SessionExerciseUiModel>,
    val restTimerSeconds: Int?,
    val isLoading: Boolean,
    val error: AppError?,
)

sealed interface ActiveSessionEvent {
    data class CompleteSet(val exerciseId: String, val weightKg: Double, val reps: Int) : ActiveSessionEvent
    data object FinishWorkout : ActiveSessionEvent
    data object DismissError : ActiveSessionEvent
}
```

**Required UI states for every screen:** `loading`, `empty`, `error`, `success`.

---

## Offline-First Policy

- All reads come from **local Room** — the app is usable without network.
- Bundled exercise catalog is seeded on first launch.
- Optional future catalog download via WorkManager does **not** block local reads.
- Sync failure never deletes existing local workout history.

---

## Error Propagation

```
DomainException (domain)
    → caught in Use Case
    → mapped to AppError (application)
    → exposed in UiState (app)
    → mapped to localized string via ErrorMessageMapper (app)
```

Never expose raw exceptions or stack traces in the UI.
