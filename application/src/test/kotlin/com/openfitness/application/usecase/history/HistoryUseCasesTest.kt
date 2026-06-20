package com.openfitness.application.usecase.history

import app.cash.turbine.test
import com.openfitness.domain.model.PersonalRecord
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.repository.PersonalRecordRepository
import com.openfitness.domain.repository.WorkoutSessionRepository
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import io.mockk.every
import io.mockk.mockk
import java.time.Instant
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class ViewWorkoutHistoryUseCaseTest {

    private val repo: WorkoutSessionRepository = mockk()
    private val useCase = ViewWorkoutHistoryUseCase(repo)

    @Test
    fun `GIVEN no completed sessions WHEN invoke THEN emits empty list`() = runTest {
        every { repo.observeCompleted(any()) } returns flowOf(emptyList())

        useCase().test {
            assertTrue(awaitItem().isEmpty())
            awaitComplete()
        }
    }

    @Test
    fun `GIVEN completed sessions WHEN invoke THEN emits sessions`() = runTest {
        val instant = Instant.parse("2026-06-19T10:00:00Z")
        val session = WorkoutSession.restore(
            id = SessionId.generate(),
            templateId = null,
            status = com.openfitness.domain.valueobject.SessionStatus.COMPLETED,
            exercises = emptyList(),
            setLogs = emptyList(),
            startedAt = instant,
            completedAt = instant,
            cancelledAt = null,
        )
        every { repo.observeCompleted(100) } returns flowOf(listOf(session))

        useCase().test {
            assertEquals(listOf(session), awaitItem())
            awaitComplete()
        }
    }
}

class ViewPersonalRecordsUseCaseTest {

    private val repo: PersonalRecordRepository = mockk()
    private val useCase = ViewPersonalRecordsUseCase(repo)

    @Test
    fun `GIVEN no records WHEN invoke THEN emits empty list`() = runTest {
        every { repo.observeAll() } returns flowOf(emptyList())

        useCase().test {
            assertTrue(awaitItem().isEmpty())
            awaitComplete()
        }
    }

    @Test
    fun `GIVEN records WHEN invoke THEN emits records`() = runTest {
        val exerciseId = ExerciseId.generate()
        val instant = Instant.parse("2026-06-19T10:00:00Z")
        val record = PersonalRecord(
            exerciseId = exerciseId,
            metric = PersonalRecordMetric.MAX_WEIGHT,
            value = 100.0,
            achievedAt = instant,
            sessionId = SessionId.generate(),
            setLogId = SetLogId.generate(),
        )
        every { repo.observeAll() } returns flowOf(listOf(record))

        useCase().test {
            assertEquals(listOf(record), awaitItem())
            awaitComplete()
        }
    }
}
