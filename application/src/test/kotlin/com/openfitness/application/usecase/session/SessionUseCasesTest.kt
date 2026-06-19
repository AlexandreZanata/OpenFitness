package com.openfitness.application.usecase.session

import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.testsupport.ImmediateTransactionRunner
import com.openfitness.domain.model.SessionExercise
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.repository.PersonalRecordRepository
import com.openfitness.domain.repository.RecordCorrectionRepository
import com.openfitness.domain.repository.SetLogRepository
import com.openfitness.domain.repository.WorkoutSessionRepository
import com.openfitness.domain.rule.PersonalRecordEvaluationRule
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.Weight
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.time.Instant

class StartWorkoutSessionUseCaseTest {

    private val sessionRepo: WorkoutSessionRepository = mockk(relaxed = true)
    private val useCase = StartWorkoutSessionUseCase(sessionRepo)
    private val exerciseId = ExerciseId.generate()

    @Test
    fun `GIVEN session in progress WHEN start THEN ConflictError`() = runTest {
        coEvery { sessionRepo.findInProgress() } returns mockk()

        val result = useCase(null, listOf(exerciseId))

        assertEquals(AppError.ConflictError, (result as UseCaseResult.Failure).error)
    }

    @Test
    fun `GIVEN empty exercises WHEN start THEN ValidationError`() = runTest {
        coEvery { sessionRepo.findInProgress() } returns null

        val result = useCase(null, emptyList())

        assertEquals(AppError.ValidationError, (result as UseCaseResult.Failure).error)
    }

    @Test
    fun `GIVEN valid exercises WHEN start THEN saves in progress session`() = runTest {
        coEvery { sessionRepo.findInProgress() } returns null

        val result = useCase(null, listOf(exerciseId))

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        coVerify { sessionRepo.save(any()) }
    }
}

class LogSetUseCaseTest {

    private val sessionRepo: WorkoutSessionRepository = mockk(relaxed = true)
    private val setLogRepo: SetLogRepository = mockk(relaxed = true)
    private val useCase = LogSetUseCase(sessionRepo, setLogRepo, ImmediateTransactionRunner())
    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T10:00:00Z")

    @Test
    fun `GIVEN invalid weight WHEN log set THEN ValidationError`() = runTest {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        coEvery { sessionRepo.findById(session.id) } returns session

        val result = useCase(session.id, exerciseId, weightKg = -5.0, reps = 8)

        assertEquals(AppError.ValidationError, (result as UseCaseResult.Failure).error)
    }

    @Test
    fun `GIVEN completed session WHEN log set THEN ValidationError`() = runTest {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        val setLog = SetLog.create(
            sessionId = session.id,
            exerciseId = exerciseId,
            setNumber = 1,
            weight = Weight.fromKilograms(50.0),
            reps = RepCount(10),
            completedAt = instant,
        )
        val completed = session.logSet(setLog).complete(instant)
        coEvery { sessionRepo.findById(completed.id) } returns completed

        val result = useCase(completed.id, exerciseId, weightKg = 60.0, reps = 5)

        assertEquals(AppError.ValidationError, (result as UseCaseResult.Failure).error)
    }

    @Test
    fun `GIVEN active session WHEN log set THEN persists set`() = runTest {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        coEvery { sessionRepo.findById(session.id) } returns session

        val result = useCase(session.id, exerciseId, weightKg = 60.0, reps = 5)

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        coVerify { sessionRepo.save(any()) }
        coVerify { setLogRepo.save(any()) }
    }
}

class CompleteWorkoutSessionUseCaseTest {

    private val sessionRepo: WorkoutSessionRepository = mockk(relaxed = true)
    private val prRepo: PersonalRecordRepository = mockk(relaxed = true)
    private val useCase = CompleteWorkoutSessionUseCase(
        sessionRepo,
        prRepo,
        PersonalRecordEvaluationRule(),
        ImmediateTransactionRunner(),
    )
    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T10:00:00Z")

    @Test
    fun `GIVEN session beating PR WHEN complete THEN returns new personal records`() = runTest {
        val sessionId = SessionId.generate()
        var session = WorkoutSession.restore(
            id = sessionId,
            templateId = null,
            status = com.openfitness.domain.valueobject.SessionStatus.IN_PROGRESS,
            exercises = listOf(SessionExercise(exerciseId, 0)),
            setLogs = emptyList(),
            startedAt = instant,
            completedAt = null,
            cancelledAt = null,
        )
        val setLog = SetLog.create(sessionId, exerciseId, 1, Weight.fromKilograms(120.0), RepCount(5), instant)
        session = session.logSet(setLog)
        coEvery { sessionRepo.findById(sessionId) } returns session
        coEvery { prRepo.findCurrent(exerciseId, any()) } returns null

        val result = useCase(sessionId)

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        assertTrue((result as UseCaseResult.Success).value.newPersonalRecords.isNotEmpty())
        coVerify { sessionRepo.save(any()) }
        coVerify { prRepo.save(any()) }
    }
}

class EditSetUseCaseTest {

    private val sessionRepo: WorkoutSessionRepository = mockk(relaxed = true)
    private val useCase = EditSetUseCase(sessionRepo, ImmediateTransactionRunner())
    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T10:00:00Z")

    @Test
    fun `GIVEN active session WHEN edit set THEN updates metrics`() = runTest {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        val setLog = SetLog.create(session.id, exerciseId, 1, Weight.fromKilograms(50.0), RepCount(10), instant)
        val withSet = session.logSet(setLog)
        coEvery { sessionRepo.findById(withSet.id) } returns withSet

        val result = useCase(withSet.id, setLog.id, weightKg = 55.0, reps = 8)

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        assertEquals(55.0, (result as UseCaseResult.Success).value.weight?.kilograms)
        coVerify { sessionRepo.save(any()) }
    }
}

class CorrectCompletedSetUseCaseTest {

    private val sessionRepo: WorkoutSessionRepository = mockk(relaxed = true)
    private val correctionRepo: RecordCorrectionRepository = mockk(relaxed = true)
    private val useCase = CorrectCompletedSetUseCase(
        sessionRepo,
        correctionRepo,
        ImmediateTransactionRunner(),
    )
    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T10:00:00Z")

    @Test
    fun `GIVEN in progress session WHEN correct THEN ValidationError`() = runTest {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        coEvery { sessionRepo.findById(session.id) } returns session

        val result = useCase(session.id, SetLogId.generate(), weightKg = 60.0, reps = 5, reason = "fix")

        assertEquals(AppError.ValidationError, (result as UseCaseResult.Failure).error)
    }

    @Test
    fun `GIVEN completed session WHEN correct THEN appends correction`() = runTest {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        val setLog = SetLog.create(
            sessionId = session.id,
            exerciseId = exerciseId,
            setNumber = 1,
            weight = Weight.fromKilograms(80.0),
            reps = RepCount(5),
            completedAt = instant,
        )
        val completed = session.logSet(setLog).complete(instant)
        coEvery { sessionRepo.findById(completed.id) } returns completed

        val result = useCase(completed.id, setLog.id, weightKg = 85.0, reps = 5, reason = "plate error")

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        coVerify { correctionRepo.save(any()) }
        coVerify(exactly = 0) { sessionRepo.save(any()) }
    }
}
