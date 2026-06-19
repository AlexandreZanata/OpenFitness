# Contract — Use Case Signatures

Application layer classes. Each use case has a single `operator fun invoke(...)`.

## Exercise Library

```kotlin
class BrowseExercisesUseCase(private val repo: ExerciseRepository) {
    operator fun invoke(query: String, filter: MuscleGroup?): Flow<List<Exercise>>
}

class CreateCustomExerciseUseCase(
    private val repo: ExerciseRepository,
    private val uniquenessRule: ExerciseNameUniquenessRule,
) {
    suspend operator fun invoke(
        name: String,
        muscleGroup: MuscleGroup,
        equipment: EquipmentType,
    ): Result<Exercise, AppError>
}
```

## Templates

```kotlin
class CreateWorkoutTemplateUseCase(private val repo: WorkoutTemplateRepository) {
    suspend operator fun invoke(
        name: String,
        exercises: List<TemplateExerciseInput>,
    ): Result<WorkoutTemplate, AppError>
}
```

## Sessions

```kotlin
class StartWorkoutSessionUseCase(
    private val sessionRepo: WorkoutSessionRepository,
) {
    suspend operator fun invoke(
        templateId: TemplateId?,
        exerciseIds: List<ExerciseId>,
    ): Result<WorkoutSession, AppError>
}

class LogSetUseCase(
    private val sessionRepo: WorkoutSessionRepository,
    private val setLogRepo: SetLogRepository,
    private val transactionRunner: TransactionRunner,
) {
    suspend operator fun invoke(
        sessionId: SessionId,
        exerciseId: ExerciseId,
        weightKg: Double?,
        reps: Int?,
    ): Result<SetLog, AppError>
}

class CompleteWorkoutSessionUseCase(
    private val sessionRepo: WorkoutSessionRepository,
    private val prRepo: PersonalRecordRepository,
    private val prRule: PersonalRecordEvaluationRule,
    private val transactionRunner: TransactionRunner,
) {
    suspend operator fun invoke(sessionId: SessionId): Result<CompletionSummary, AppError>
}
```

## History & PRs

```kotlin
class ViewWorkoutHistoryUseCase(private val repo: WorkoutSessionRepository) {
    operator fun invoke(): Flow<List<WorkoutSession>>
}

class ViewPersonalRecordsUseCase(private val repo: PersonalRecordRepository) {
    operator fun invoke(): Flow<List<PersonalRecord>>
}
```

## Record Editing

```kotlin
class EditSetUseCase(
    private val sessionRepo: WorkoutSessionRepository,
    private val transactionRunner: TransactionRunner,
) {
    suspend operator fun invoke(
        sessionId: SessionId,
        setLogId: SetLogId,
        weightKg: Double?,
        reps: Int?,
    ): Result<SetLog, AppError>
}

class UpdateWorkoutTemplateUseCase(private val repo: WorkoutTemplateRepository) {
    suspend operator fun invoke(
        templateId: TemplateId,
        name: String?,
        exercises: List<TemplateExerciseInput>?,
    ): Result<WorkoutTemplate, AppError>
}

class UpdateCustomExerciseUseCase(
    private val repo: ExerciseRepository,
    private val uniquenessRule: ExerciseNameUniquenessRule,
) {
    suspend operator fun invoke(
        exerciseId: ExerciseId,
        name: String,
        muscleGroup: MuscleGroup,
        equipment: EquipmentType,
    ): Result<Exercise, AppError>
}

class CorrectCompletedSetUseCase(
    private val sessionRepo: WorkoutSessionRepository,
    private val correctionRepo: RecordCorrectionRepository,
    private val transactionRunner: TransactionRunner,
) {
    suspend operator fun invoke(
        sessionId: SessionId,
        originalSetLogId: SetLogId,
        weightKg: Double?,
        reps: Int?,
        reason: String?,
    ): Result<RecordCorrection, AppError>
}
```

## Result Type

```kotlin
typealias UseCaseResult<T> = Result<T, AppError>
```

Domain exceptions are caught inside use cases and mapped to `AppError` — never leaked to UI raw.
