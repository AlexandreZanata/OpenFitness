package com.openfitness.domain.repository

import com.openfitness.domain.model.Exercise
import com.openfitness.domain.model.RecordCorrection
import com.openfitness.domain.model.PersonalRecord
import com.openfitness.domain.model.PersonalRecordHistoryEntry
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.model.WorkoutTemplate
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.TemplateId
import kotlinx.coroutines.flow.Flow

interface ExerciseRepository {
    suspend fun findById(id: ExerciseId): Exercise?
    suspend fun search(query: String, muscleGroup: MuscleGroup?): List<Exercise>
    suspend fun findAllNames(): List<String>
    suspend fun save(exercise: Exercise)
    fun observeAll(): Flow<List<Exercise>>
}

interface WorkoutTemplateRepository {
    suspend fun findById(id: TemplateId): WorkoutTemplate?
    suspend fun save(template: WorkoutTemplate)
    suspend fun delete(id: TemplateId)
    fun observeAll(): Flow<List<WorkoutTemplate>>
}

interface WorkoutSessionRepository {
    suspend fun findById(id: SessionId): WorkoutSession?
    suspend fun findInProgress(): WorkoutSession?
    suspend fun save(session: WorkoutSession)
    fun observeCompleted(limit: Int): Flow<List<WorkoutSession>>
}

interface SetLogRepository {
    suspend fun findBySession(sessionId: SessionId): List<SetLog>
    suspend fun save(setLog: SetLog)
    suspend fun saveAll(setLogs: List<SetLog>)
}

interface PersonalRecordRepository {
    suspend fun findCurrent(exerciseId: ExerciseId, metric: PersonalRecordMetric): PersonalRecord?
    suspend fun save(record: PersonalRecord)
    suspend fun saveHistory(entry: PersonalRecordHistoryEntry)
    fun observeAll(): Flow<List<PersonalRecord>>
}

interface RecordCorrectionRepository {
    suspend fun findBySession(sessionId: SessionId): List<RecordCorrection>
    suspend fun save(correction: RecordCorrection)
}

interface CatalogSeeder {
    suspend fun seedIfEmpty()
    suspend fun isSeeded(): Boolean
}

interface UserPreferencesRepository {
    fun observeRestTimerSeconds(): Flow<Int>
}

interface TransactionRunner {
    suspend fun <T> run(block: suspend () -> T): T
}
