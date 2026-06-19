package com.openfitness.domain.event

import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.TemplateId
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotEquals
import org.junit.jupiter.api.Test
import java.time.Instant
import java.util.UUID

class DomainEventCoverageTest {

    private val instant = Instant.parse("2026-06-19T14:00:00Z")
    private val sessionId = SessionId.generate()
    private val exerciseId = ExerciseId.generate()
    private val setLogId = SetLogId.generate()
    private val eventId = UUID.randomUUID()

    @Test
    fun `all domain events expose aggregate id`() {
        val started = WorkoutSessionStarted(
            eventId = eventId,
            occurredAt = instant,
            sessionId = sessionId,
            templateId = TemplateId.generate(),
            exerciseIds = listOf(exerciseId),
            startedAt = instant,
        )
        assertEquals(sessionId.toString(), started.aggregateId)

        val logged = SetLogged(
            eventId = eventId,
            occurredAt = instant,
            sessionId = sessionId,
            setLogId = setLogId,
            exerciseId = exerciseId,
            setNumber = 1,
            weightKg = 50.0,
            reps = 10,
            completedAt = instant,
        )
        assertEquals(sessionId.toString(), logged.aggregateId)

        val updated = SetLogUpdated(
            eventId = eventId,
            occurredAt = instant,
            sessionId = sessionId,
            setLogId = setLogId,
            weightKg = 55.0,
            reps = 8,
        )
        assertEquals(sessionId.toString(), updated.aggregateId)

        val completed = WorkoutSessionCompleted(
            eventId = eventId,
            occurredAt = instant,
            sessionId = sessionId,
            completedAt = instant,
            totalSets = 3,
            durationSeconds = 120,
        )
        assertEquals(sessionId.toString(), completed.aggregateId)

        val pr = PersonalRecordAchieved(
            eventId = eventId,
            occurredAt = instant,
            exerciseId = exerciseId,
            metric = PersonalRecordMetric.MAX_WEIGHT,
            previousValue = 90.0,
            newValue = 100.0,
            sessionId = sessionId,
            setLogId = setLogId,
            achievedAt = instant,
        )
        assertEquals("${exerciseId}_${PersonalRecordMetric.MAX_WEIGHT}", pr.aggregateId)
        assertNotEquals(newEventId(), eventId)
    }
}
