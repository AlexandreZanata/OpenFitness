package com.openfitness.domain.rule

import com.openfitness.domain.model.PersonalRecordAggregate
import com.openfitness.domain.model.PersonalRecordUpdateResult
import com.openfitness.domain.model.SessionExercise
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import java.time.Instant

class PersonalRecordEvaluationRuleTest {

    private val rule = PersonalRecordEvaluationRule()
    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T12:00:00Z")

    @Test
    fun `GIVEN InProgress session WHEN evaluate THEN no PR update`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
        val results = rule.evaluate(session, emptyMap(), instant)
        assertTrue(results.isEmpty())
    }

    @Test
    fun `GIVEN cancelled session WHEN evaluate THEN no PR update`() {
        val sessionId = com.openfitness.domain.valueobject.SessionId.generate()
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
        session = session.logSet(setLog).cancel(instant)
        val results = rule.evaluate(session, emptyMap(), instant)
        assertTrue(results.isEmpty())
    }

    @Test
    fun `GIVEN completed session beating PR WHEN evaluate THEN NewRecord`() {
        val sessionId = com.openfitness.domain.valueobject.SessionId.generate()
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
        session = session.logSet(setLog).complete(instant)
        val results = rule.evaluate(session, emptyMap(), instant)
        assertTrue(results.any { it is PersonalRecordUpdateResult.NewRecord })
    }

    @Test
    fun `GIVEN existing PR higher WHEN evaluate THEN NoChange`() {
        val sessionId = com.openfitness.domain.valueobject.SessionId.generate()
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
        val setLog = SetLog.create(sessionId, exerciseId, 1, Weight.fromKilograms(80.0), RepCount(5), instant)
        session = session.logSet(setLog).complete(instant)
        val keyWeight = exerciseId.toString() to PersonalRecordMetric.MAX_WEIGHT
        val keyReps = exerciseId.toString() to PersonalRecordMetric.MAX_REPS
        val current = mapOf(
            keyWeight to PersonalRecordAggregate(
                com.openfitness.domain.model.PersonalRecord(
                    exerciseId = exerciseId,
                    metric = PersonalRecordMetric.MAX_WEIGHT,
                    value = 100.0,
                    achievedAt = instant,
                    sessionId = sessionId,
                    setLogId = setLog.id,
                ),
            ),
            keyReps to PersonalRecordAggregate(
                com.openfitness.domain.model.PersonalRecord(
                    exerciseId = exerciseId,
                    metric = PersonalRecordMetric.MAX_REPS,
                    value = 20.0,
                    achievedAt = instant,
                    sessionId = sessionId,
                    setLogId = setLog.id,
                ),
            ),
        )
        val results = rule.evaluate(session, current, instant)
        assertTrue(results.isEmpty())
    }
}
