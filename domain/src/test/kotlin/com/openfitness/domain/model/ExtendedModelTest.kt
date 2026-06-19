package com.openfitness.domain.model

import com.openfitness.domain.event.PersonalRecordAchieved
import com.openfitness.domain.event.WorkoutSessionCompleted
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionStatus
import com.openfitness.domain.valueobject.Weight
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Test
import java.time.Instant

class WorkoutTemplateExtendedTest {

    private val exerciseA = ExerciseId.generate()
    private val exerciseB = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T08:00:00Z")

    @Test
    fun `GIVEN template WHEN add and remove exercise THEN updated`() {
        val template = WorkoutTemplate.create(
            "Push",
            listOf(TemplateExercise(exerciseA, 0, 3)),
        )
        val withB = template.addExercise(exerciseB, 4, updatedAt = instant)
        assertEquals(2, withB.exercises.size)
        val withoutA = withB.removeExercise(exerciseA, instant)
        assertEquals(1, withoutA.exercises.size)
        assertEquals(0, withoutA.exercises.first().order)
    }

    @Test
    fun `GIVEN template WHEN rename THEN name updated`() {
        val template = WorkoutTemplate.create("Old", listOf(TemplateExercise(exerciseA, 0, 3)))
        val renamed = template.rename("New Name", instant)
        assertEquals("New Name", renamed.name)
    }
}

class WorkoutSessionExtendedTest {

    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T09:00:00Z")

    @Test
    fun `GIVEN IN_PROGRESS WHEN cancel THEN CANCELLED`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
            .cancel(instant)
        assertEquals(SessionStatus.CANCELLED, session.status)
    }

    @Test
    fun `GIVEN IN_PROGRESS WHEN complete THEN WorkoutSessionCompleted`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
            .complete(instant)
        assertEquals(SessionStatus.COMPLETED, session.status)
        assertInstanceOf(WorkoutSessionCompleted::class.java, session.events.last())
    }
}

class PersonalRecordExtendedTest {

    @Test
    fun `GIVEN higher value WHEN tryUpdate THEN NewRecord with event`() {
        val exerciseId = ExerciseId.generate()
        val result = PersonalRecordAggregate(null).tryUpdate(
            PersonalRecordCandidate(
                exerciseId = exerciseId,
                metric = PersonalRecordMetric.MAX_WEIGHT,
                value = 140.0,
                sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
                setLogId = com.openfitness.domain.valueobject.SetLogId.generate(),
                achievedAt = Instant.now(),
            ),
        )
        assertInstanceOf(PersonalRecordUpdateResult.NewRecord::class.java, result)
        val newRecord = result as PersonalRecordUpdateResult.NewRecord
        assertInstanceOf(PersonalRecordAchieved::class.java, newRecord.event)
        assertEquals(140.0, newRecord.record.value)
    }
}
