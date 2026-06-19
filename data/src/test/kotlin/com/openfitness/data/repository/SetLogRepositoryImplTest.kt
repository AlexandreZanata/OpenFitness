package com.openfitness.data.repository

import com.openfitness.data.local.dao.SetLogDao
import com.openfitness.data.local.dao.WorkoutSessionDao
import com.openfitness.data.local.entity.WorkoutSessionEntity
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.Weight
import io.mockk.coEvery
import io.mockk.mockk
import java.time.Instant
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class SetLogRepositoryImplTest {

    private val setLogDao: SetLogDao = mockk(relaxed = true)
    private val sessionDao: WorkoutSessionDao = mockk()
    private val repository = SetLogRepositoryImpl(setLogDao, sessionDao)

    @Test
    fun `GIVEN completed session WHEN save set THEN ImmutableRecordException`() = runTest {
        val sessionId = SessionId.generate()
        coEvery { sessionDao.findById(sessionId.toString()) } returns WorkoutSessionEntity(
            id = sessionId.toString(),
            templateId = null,
            status = "COMPLETED",
            startedAt = 1L,
            completedAt = 2L,
            cancelledAt = null,
        )
        val setLog = SetLog.create(
            sessionId = sessionId,
            exerciseId = ExerciseId.generate(),
            setNumber = 1,
            weight = Weight.fromKilograms(40.0),
            reps = RepCount(8),
            completedAt = Instant.now(),
        )
        assertThrows(ImmutableRecordException::class.java) {
            kotlinx.coroutines.runBlocking { repository.save(setLog) }
        }
    }
}
