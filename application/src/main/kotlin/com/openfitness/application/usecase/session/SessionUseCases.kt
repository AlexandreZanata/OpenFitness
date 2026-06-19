package com.openfitness.application.usecase.session

import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.error.runUseCase
import com.openfitness.application.model.CompletionSummary
import com.openfitness.application.usecase.parseReps
import com.openfitness.application.usecase.parseWeight
import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.RecordNotFoundException
import com.openfitness.domain.model.PersonalRecordAggregate
import com.openfitness.domain.model.PersonalRecordHistoryEntry
import com.openfitness.domain.model.PersonalRecordUpdateResult
import com.openfitness.domain.model.RecordCorrection
import com.openfitness.domain.model.SessionExercise
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.repository.PersonalRecordRepository
import com.openfitness.domain.repository.RecordCorrectionRepository
import com.openfitness.domain.repository.SetLogRepository
import com.openfitness.domain.repository.TransactionRunner
import com.openfitness.domain.repository.WorkoutSessionRepository
import com.openfitness.domain.rule.PersonalRecordEvaluationRule
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SessionStatus
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.TemplateId
import java.time.Instant
import java.util.UUID

class StartWorkoutSessionUseCase(
    private val sessionRepo: WorkoutSessionRepository,
) {
    suspend operator fun invoke(
        templateId: TemplateId?,
        exerciseIds: List<ExerciseId>,
    ): UseCaseResult<WorkoutSession> {
        if (sessionRepo.findInProgress() != null) {
            return UseCaseResult.failure(AppError.ConflictError)
        }
        return runUseCase {
            if (exerciseIds.isEmpty()) {
                throw DomainException("Session must have at least one exercise")
            }
            val exercises = exerciseIds.mapIndexed { index, id -> SessionExercise(id, index) }
            val started = WorkoutSession.create(templateId, exercises).start(Instant.now())
            sessionRepo.save(started)
            started
        }
    }
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
    ): UseCaseResult<SetLog> = runUseCase {
        transactionRunner.run {
            val session = sessionRepo.findById(sessionId)
                ?: throw RecordNotFoundException(sessionId.toString())
            val weight = parseWeight(weightKg)
            val repCount = parseReps(reps)
            val setNumber = session.setLogs.count { it.exerciseId == exerciseId } + 1
            val setLog = SetLog.create(
                sessionId = sessionId,
                exerciseId = exerciseId,
                setNumber = setNumber,
                weight = weight,
                reps = repCount,
                completedAt = Instant.now(),
            )
            val updated = session.logSet(setLog)
            sessionRepo.save(updated)
            setLogRepo.save(setLog)
            setLog
        }
    }
}

class CompleteWorkoutSessionUseCase(
    private val sessionRepo: WorkoutSessionRepository,
    private val prRepo: PersonalRecordRepository,
    private val prRule: PersonalRecordEvaluationRule,
    private val transactionRunner: TransactionRunner,
) {
    suspend operator fun invoke(sessionId: SessionId): UseCaseResult<CompletionSummary> = runUseCase {
        transactionRunner.run {
            val session = sessionRepo.findById(sessionId)
                ?: throw RecordNotFoundException(sessionId.toString())
            val completedAt = Instant.now()
            val completed = session.complete(completedAt)
            val currentRecords = loadCurrentRecords(completed)
            val prResults = prRule.evaluate(completed, currentRecords, completedAt)
            val newRecords = mutableListOf<com.openfitness.domain.model.PersonalRecord>()

            for (result in prResults) {
                if (result is PersonalRecordUpdateResult.NewRecord) {
                    val key = result.record.exerciseId.toString() to result.record.metric
                    currentRecords[key]?.current?.let { previous ->
                        prRepo.saveHistory(
                            PersonalRecordHistoryEntry(
                                id = UUID.randomUUID().toString(),
                                exerciseId = previous.exerciseId,
                                metric = previous.metric,
                                value = previous.value,
                                achievedAt = previous.achievedAt,
                                sessionId = previous.sessionId,
                                setLogId = previous.setLogId,
                                supersededAt = completedAt,
                            ),
                        )
                    }
                    prRepo.save(result.record)
                    newRecords.add(result.record)
                }
            }

            sessionRepo.save(completed)
            CompletionSummary(session = completed, newPersonalRecords = newRecords)
        }
    }

    private suspend fun loadCurrentRecords(
        session: WorkoutSession,
    ): Map<Pair<String, PersonalRecordMetric>, PersonalRecordAggregate> {
        val records = mutableMapOf<Pair<String, PersonalRecordMetric>, PersonalRecordAggregate>()
        for (exercise in session.exercises) {
            for (metric in PersonalRecordMetric.entries) {
                prRepo.findCurrent(exercise.exerciseId, metric)?.let { current ->
                    records[exercise.exerciseId.toString() to metric] = PersonalRecordAggregate(current)
                }
            }
        }
        return records
    }
}

class EditSetUseCase(
    private val sessionRepo: WorkoutSessionRepository,
    private val transactionRunner: TransactionRunner,
) {
    suspend operator fun invoke(
        sessionId: SessionId,
        setLogId: SetLogId,
        weightKg: Double?,
        reps: Int?,
    ): UseCaseResult<SetLog> = runUseCase {
        transactionRunner.run {
            val session = sessionRepo.findById(sessionId)
                ?: throw RecordNotFoundException(sessionId.toString())
            val weight = parseWeight(weightKg)
            val repCount = parseReps(reps)
            val updated = session.updateSetLog(setLogId, weight, repCount, Instant.now())
            sessionRepo.save(updated)
            updated.setLogs.first { it.id == setLogId }
        }
    }
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
    ): UseCaseResult<RecordCorrection> = runUseCase {
        transactionRunner.run {
            val session = sessionRepo.findById(sessionId)
                ?: throw RecordNotFoundException(sessionId.toString())
            if (session.status != SessionStatus.COMPLETED) {
                throw DomainException("Corrections apply only to completed sessions")
            }
            if (session.setLogs.none { it.id == originalSetLogId }) {
                throw RecordNotFoundException(originalSetLogId.toString())
            }
            val correction = RecordCorrection.create(
                sessionId = sessionId,
                originalSetLogId = originalSetLogId,
                correctedWeight = parseWeight(weightKg),
                correctedReps = parseReps(reps),
                reason = reason,
            )
            correctionRepo.save(correction)
            correction
        }
    }
}
