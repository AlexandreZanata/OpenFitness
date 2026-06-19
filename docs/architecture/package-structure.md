# Package Structure

Canonical package layout per module. All packages live under `com.openfitness`.

## `:domain` — `com.openfitness.domain`

```
domain/
├── model/
│   ├── Exercise.kt
│   ├── WorkoutTemplate.kt
│   ├── WorkoutSession.kt
│   ├── SetLog.kt
│   └── PersonalRecord.kt
├── valueobject/
│   ├── ExerciseId.kt
│   ├── SessionId.kt
│   ├── Weight.kt
│   ├── RepCount.kt
│   ├── Duration.kt
│   └── MuscleGroup.kt
├── rule/
│   ├── ExerciseNameUniquenessRule.kt      # BR-001
│   ├── PositiveSetValuesRule.kt           # BR-002
│   ├── SessionMustHaveExercisesRule.kt    # BR-003
│   └── CompletedSetRequiresMetricsRule.kt # BR-004
├── state/
│   └── WorkoutSessionStateMachine.kt
├── event/
│   ├── WorkoutSessionStarted.kt
│   ├── SetLogged.kt
│   ├── WorkoutSessionCompleted.kt
│   └── PersonalRecordAchieved.kt
├── repository/
│   ├── ExerciseRepository.kt
│   ├── WorkoutTemplateRepository.kt
│   ├── WorkoutSessionRepository.kt
│   ├── SetLogRepository.kt
│   └── PersonalRecordRepository.kt
└── exception/
    ├── DomainException.kt
    ├── InvalidStateTransitionException.kt
    └── DuplicateExerciseNameException.kt
```

## `:application` — `com.openfitness.application`

```
application/
├── usecase/
│   ├── exerciselibrary/
│   │   ├── BrowseExercisesUseCase.kt
│   │   └── CreateCustomExerciseUseCase.kt
│   ├── template/
│   │   ├── CreateWorkoutTemplateUseCase.kt
│   │   └── ListWorkoutTemplatesUseCase.kt
│   ├── session/
│   │   ├── StartWorkoutSessionUseCase.kt
│   │   ├── LogSetUseCase.kt
│   │   └── CompleteWorkoutSessionUseCase.kt
│   └── history/
│       ├── ViewWorkoutHistoryUseCase.kt
│       └── ViewPersonalRecordsUseCase.kt
├── error/
│   └── AppError.kt
└── dispatcher/
    └── DispatcherProvider.kt
```

## `:data` — `com.openfitness.data`

```
data/
├── local/
│   ├── OpenFitnessDatabase.kt
│   ├── dao/
│   ├── entity/
│   └── migration/
├── preferences/
│   └── UserPreferencesDataStore.kt
├── mapper/
├── repository/
├── worker/
│   └── RestReminderWorker.kt
├── parser/
│   └── BundledExerciseCatalogParser.kt
└── di/
    └── DataModule.kt
```

## `:app` — `com.openfitness.app`

```
app/
├── OpenFitnessApplication.kt
├── navigation/
│   ├── OpenFitnessNavHost.kt
│   └── Routes.kt
├── theme/
│   ├── Color.kt
│   ├── Type.kt
│   └── Theme.kt
├── feature/
│   ├── exerciselibrary/
│   │   ├── ExerciseLibraryScreen.kt
│   │   ├── ExerciseLibraryViewModel.kt
│   │   └── ExerciseLibraryUiState.kt
│   ├── activesession/
│   ├── history/
│   └── personalrecords/
├── common/
│   ├── error/
│   │   └── ErrorMessageMapper.kt
│   └── component/
└── di/
    ├── AppModule.kt
    └── UseCaseModule.kt
```

## Naming Conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| Entity | noun, singular | `WorkoutSession` |
| Value Object | noun or measured quantity | `RepCount` |
| Use case | verb phrase + `UseCase` | `LogSetUseCase` |
| Repository port | noun + `Repository` | `SetLogRepository` |
| Domain event | past tense phrase | `SetLogged` |
| Business rule | descriptive + `Rule` | `PositiveSetValuesRule` |
| ViewModel | feature + `ViewModel` | `ActiveSessionViewModel` |
| UiState | feature + `UiState` | `ActiveSessionUiState` |
| UiEvent | feature + `Event` (sealed) | `ActiveSessionEvent` |
