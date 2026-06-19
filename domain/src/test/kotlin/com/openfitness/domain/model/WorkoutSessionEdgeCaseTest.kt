package com.openfitness.domain.model

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.RecordNotFoundException
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test
import java.time.Instant

class WorkoutSessionEdgeCaseTest {

    private val exerciseId = ExerciseId.generate()
    private val otherExerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T11:00:00Z")

    @Test
    fun `GIVEN unknown set id WHEN updateSetLog THEN RecordNotFoundException`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        assertThrows(RecordNotFoundException::class.java) {
            session.updateSetLog(
                com.openfitness.domain.valueobject.SetLogId.generate(),
                Weight.fromKilograms(50.0),
                RepCount(10),
                instant,
            )
        }
    }

    @Test
    fun `GIVEN set for foreign session WHEN logSet THEN DomainException`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        val foreignSet = SetLog.create(
            sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
            exerciseId = exerciseId,
            setNumber = 1,
            weight = Weight.fromKilograms(40.0),
            reps = RepCount(8),
            completedAt = instant,
        )
        assertThrows(DomainException::class.java) {
            session.logSet(foreignSet)
        }
    }

    @Test
    fun `GIVEN exercise not in session WHEN logSet THEN DomainException`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0))).start(instant)
        val setLog = SetLog.create(session.id, otherExerciseId, 1, Weight.fromKilograms(30.0), RepCount(6), instant)
        assertThrows(DomainException::class.java) {
            session.logSet(setLog)
        }
    }

    @Test
    fun `GIVEN PLANNED session WHEN cancel THEN CANCELLED`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .cancel(instant)
        assertEquals(com.openfitness.domain.valueobject.SessionStatus.CANCELLED, session.status)
    }

    @Test
    fun `GIVEN set with weight only WHEN create THEN accepted`() {
        SetLog.create(
            sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
            exerciseId = exerciseId,
            setNumber = 1,
            weight = Weight.fromKilograms(100.0),
            reps = null,
            completedAt = instant,
        )
    }

    @Test
    fun `GIVEN template duplicate exercise WHEN addExercise THEN DomainException`() {
        val template = WorkoutTemplate.create("Legs", listOf(TemplateExercise(exerciseId, 0, 3)))
        assertThrows(DomainException::class.java) {
            template.addExercise(exerciseId, 3, updatedAt = instant)
        }
    }
}

private fun assertEquals(expected: Any?, actual: Any?) {
    org.junit.jupiter.api.Assertions.assertEquals(expected, actual)
}
