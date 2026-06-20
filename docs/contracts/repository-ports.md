# Contract — Repository Ports

Interfaces defined in `:domain`. Implementations in `:data`.

## ExerciseRepository

```kotlin
interface ExerciseRepository {
    suspend fun findById(id: ExerciseId): Exercise?
    suspend fun search(query: String, muscleGroup: MuscleGroup?): List<Exercise>
    suspend fun findAllNames(): List<String>           // for BR-001
    suspend fun save(exercise: Exercise)
    fun observeAll(): Flow<List<Exercise>>
}
```

## WorkoutTemplateRepository

```kotlin
interface WorkoutTemplateRepository {
    suspend fun findById(id: TemplateId): WorkoutTemplate?
    suspend fun save(template: WorkoutTemplate)
    suspend fun delete(id: TemplateId)
    fun observeAll(): Flow<List<WorkoutTemplate>>
}
```

## WorkoutSessionRepository

```kotlin
interface WorkoutSessionRepository {
    suspend fun findById(id: SessionId): WorkoutSession?
    suspend fun findInProgress(): WorkoutSession?
    suspend fun save(session: WorkoutSession)
    fun observeCompleted(limit: Int): Flow<List<WorkoutSession>>
}
```

## SetLogRepository

```kotlin
interface SetLogRepository {
    suspend fun findBySession(sessionId: SessionId): List<SetLog>
    suspend fun save(setLog: SetLog)
    suspend fun saveAll(setLogs: List<SetLog>)
}
```

## PersonalRecordRepository

```kotlin
interface PersonalRecordRepository {
    suspend fun findCurrent(exerciseId: ExerciseId, metric: PersonalRecordMetric): PersonalRecord?
    suspend fun save(record: PersonalRecord)
    suspend fun saveHistory(entry: PersonalRecordHistoryEntry)
    fun observeAll(): Flow<List<PersonalRecord>>
}
```

## RecordCorrectionRepository

```kotlin
interface RecordCorrectionRepository {
    suspend fun findBySession(sessionId: SessionId): List<RecordCorrection>
    suspend fun save(correction: RecordCorrection)
}
```

Append-only persistence for BR-009. No update or delete methods.

## UserPreferencesRepository

```kotlin
interface UserPreferencesRepository {
    fun observeRestTimerSeconds(): Flow<Int>
}
```

Implemented in `:data` via DataStore. Keys defined in [database-schema.md](database-schema.md) § DataStore Preferences.

## CatalogSeeder (infrastructure port)

```kotlin
interface CatalogSeeder {
    suspend fun seedIfEmpty()
    suspend fun isSeeded(): Boolean
}
```

Defined in `:domain` as port; implemented in `:data` using bundled JSON parser.

## Transaction Boundary

Multi-entity writes (session + set logs + PR updates) use a `TransactionRunner` port:

```kotlin
interface TransactionRunner {
    suspend fun <T> run(block: suspend () -> T): T
}
```
