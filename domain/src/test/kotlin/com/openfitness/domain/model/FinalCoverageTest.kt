package com.openfitness.domain.model

import com.openfitness.domain.state.WorkoutSessionStateMachine
import com.openfitness.domain.valueobject.SessionStatus
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.time.Instant

class FinalCoverageTest {

    @Test
    fun `state machine isValid returns false for invalid transition`() {
        assertFalse(WorkoutSessionStateMachine.isValid(SessionStatus.COMPLETED, SessionStatus.PLANNED))
    }

    @Test
    fun `state machine isTerminal false for in progress`() {
        assertFalse(WorkoutSessionStateMachine.isTerminal(SessionStatus.IN_PROGRESS))
    }

    @Test
    fun `state machine isTerminal true for cancelled`() {
        assertTrue(WorkoutSessionStateMachine.isTerminal(SessionStatus.CANCELLED))
    }

    @Test
    fun `GIVEN invalid template exercise order WHEN create THEN fails`() {
        assertThrows(IllegalArgumentException::class.java) {
            TemplateExercise(com.openfitness.domain.valueobject.ExerciseId.generate(), -1, 3)
        }
    }

    @Test
    fun `GIVEN invalid session exercise order WHEN create THEN fails`() {
        assertThrows(IllegalArgumentException::class.java) {
            SessionExercise(com.openfitness.domain.valueobject.ExerciseId.generate(), -1)
        }
    }

    @Test
    fun `GIVEN zero PR candidate WHEN tryUpdate THEN NoChange`() {
        val result = PersonalRecordAggregate(null).tryUpdate(
            PersonalRecordCandidate(
                exerciseId = com.openfitness.domain.valueobject.ExerciseId.generate(),
                metric = com.openfitness.domain.valueobject.PersonalRecordMetric.MAX_WEIGHT,
                value = 0.0,
                sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
                setLogId = com.openfitness.domain.valueobject.SetLogId.generate(),
                achievedAt = Instant.now(),
            ),
        )
        assertTrue(result is PersonalRecordUpdateResult.NoChange)
    }

    @Test
    fun `GIVEN session with events WHEN consumeEvents THEN cleared`() {
        val instant = Instant.now()
        val exerciseId = com.openfitness.domain.valueobject.ExerciseId.generate()
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
        assertTrue(session.events.isNotEmpty())
        val consumed = session.consumeEvents()
        assertTrue(consumed.isNotEmpty())
        assertTrue(session.events.isEmpty())
    }

    @Test
    fun `GIVEN invalid personal record WHEN create THEN fails`() {
        assertThrows(IllegalArgumentException::class.java) {
            PersonalRecord(
                exerciseId = com.openfitness.domain.valueobject.ExerciseId.generate(),
                metric = com.openfitness.domain.valueobject.PersonalRecordMetric.MAX_WEIGHT,
                value = 0.0,
                achievedAt = Instant.now(),
                sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
                setLogId = com.openfitness.domain.valueobject.SetLogId.generate(),
            )
        }
    }
}
