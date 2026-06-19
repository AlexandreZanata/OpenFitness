package com.openfitness.domain.rule

import com.openfitness.domain.model.PersonalRecordUpdateResult
import com.openfitness.domain.model.SessionExercise
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.time.Instant

class PersonalRecordEvaluationRuleExtendedTest {

    private val rule = PersonalRecordEvaluationRule()

    @Test
    fun `evaluateSetsOnly returns false for empty list`() {
        assertFalse(rule.evaluateSetsOnly(emptyList()))
    }

    @Test
    fun `evaluateSetsOnly returns true when sets present`() {
        val set = SetLog.create(
            sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
            exerciseId = ExerciseId.generate(),
            setNumber = 1,
            weight = Weight.fromKilograms(50.0),
            reps = RepCount(10),
            completedAt = Instant.now(),
        )
        assertTrue(rule.evaluateSetsOnly(listOf(set)))
    }

    @Test
    fun `GIVEN reps only sets WHEN evaluate THEN may produce MAX_REPS`() {
        val exerciseId = ExerciseId.generate()
        val sessionId = com.openfitness.domain.valueobject.SessionId.generate()
        val instant = Instant.now()
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
        session = session.logSet(
            SetLog.create(sessionId, exerciseId, 1, null, RepCount(15), instant),
        )
        val results = rule.evaluate(session, emptyMap(), instant)
        assertTrue(results.isNotEmpty())
        assertTrue(results.all { it is PersonalRecordUpdateResult.NewRecord })
    }
}
