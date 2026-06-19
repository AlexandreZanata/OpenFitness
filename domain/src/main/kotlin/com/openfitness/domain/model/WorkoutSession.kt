package com.openfitness.domain.model

import com.openfitness.domain.event.DomainEvent
import com.openfitness.domain.event.SetLogged
import com.openfitness.domain.event.SetLogUpdated
import com.openfitness.domain.event.WorkoutSessionCompleted
import com.openfitness.domain.event.WorkoutSessionStarted
import com.openfitness.domain.event.newEventId
import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.exception.RecordNotFoundException
import com.openfitness.domain.rule.SessionMustHaveExercisesRule
import com.openfitness.domain.rule.SetEditableInProgressOnlyRule
import com.openfitness.domain.state.WorkoutSessionStateMachine
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SessionStatus
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.TemplateId
import com.openfitness.domain.valueobject.Weight
import java.time.Instant

class WorkoutSession private constructor(
    val id: SessionId,
    val templateId: TemplateId?,
    val status: SessionStatus,
    val exercises: List<SessionExercise>,
    val setLogs: List<SetLog>,
    val startedAt: Instant?,
    val completedAt: Instant?,
    val cancelledAt: Instant?,
    private val pendingEvents: MutableList<DomainEvent>,
) {
    val events: List<DomainEvent> get() = pendingEvents.toList()

    fun consumeEvents(): List<DomainEvent> = pendingEvents.toList().also { pendingEvents.clear() }

    fun start(at: Instant): WorkoutSession {
        ensureMutable()
        WorkoutSessionStateMachine.transition(status, SessionStatus.IN_PROGRESS)
        SessionMustHaveExercisesRule().validate(exercises.size)
        val updated = copy(
            status = SessionStatus.IN_PROGRESS,
            startedAt = at,
        )
        updated.pendingEvents.add(
            WorkoutSessionStarted(
                eventId = newEventId(),
                occurredAt = at,
                sessionId = id,
                templateId = templateId,
                exerciseIds = exercises.map { it.exerciseId },
                startedAt = at,
            ),
        )
        return updated
    }

    fun logSet(setLog: SetLog): WorkoutSession {
        ensureInProgress()
        if (setLog.sessionId != id) {
            throw DomainException("Set log session id mismatch")
        }
        if (exercises.none { it.exerciseId == setLog.exerciseId }) {
            throw DomainException("Exercise not part of session")
        }
        val updated = copy(setLogs = setLogs + setLog)
        updated.pendingEvents.add(
            SetLogged(
                eventId = newEventId(),
                occurredAt = setLog.completedAt,
                sessionId = id,
                setLogId = setLog.id,
                exerciseId = setLog.exerciseId,
                setNumber = setLog.setNumber,
                weightKg = setLog.weight?.kilograms,
                reps = setLog.reps?.value,
                completedAt = setLog.completedAt,
            ),
        )
        return updated
    }

    fun updateSetLog(
        setLogId: SetLogId,
        weight: Weight?,
        reps: RepCount?,
        updatedAt: Instant,
    ): WorkoutSession {
        SetEditableInProgressOnlyRule().validate(status)
        val index = setLogs.indexOfFirst { it.id == setLogId }
        if (index < 0) {
            throw RecordNotFoundException(setLogId.toString())
        }
        val updatedLog = setLogs[index].withMetrics(weight, reps, updatedAt)
        val newLogs = setLogs.toMutableList().apply { this[index] = updatedLog }
        val updated = copy(setLogs = newLogs)
        updated.pendingEvents.add(
            SetLogUpdated(
                eventId = newEventId(),
                occurredAt = updatedAt,
                sessionId = id,
                setLogId = setLogId,
                weightKg = weight?.kilograms,
                reps = reps?.value,
            ),
        )
        return updated
    }

    fun complete(at: Instant): WorkoutSession {
        ensureInProgress()
        WorkoutSessionStateMachine.transition(status, SessionStatus.COMPLETED)
        val duration = startedAt?.let { at.epochSecond - it.epochSecond } ?: 0L
        val updated = copy(
            status = SessionStatus.COMPLETED,
            completedAt = at,
        )
        updated.pendingEvents.add(
            WorkoutSessionCompleted(
                eventId = newEventId(),
                occurredAt = at,
                sessionId = id,
                completedAt = at,
                totalSets = setLogs.size,
                durationSeconds = duration,
            ),
        )
        return updated
    }

    fun cancel(at: Instant): WorkoutSession {
        ensureMutable()
        WorkoutSessionStateMachine.transition(status, SessionStatus.CANCELLED)
        return copy(
            status = SessionStatus.CANCELLED,
            cancelledAt = at,
        )
    }

    companion object {
        fun create(
            templateId: TemplateId?,
            exercises: List<SessionExercise>,
        ): WorkoutSession {
            SessionMustHaveExercisesRule().validate(exercises.size)
            return WorkoutSession(
                id = SessionId.generate(),
                templateId = templateId,
                status = SessionStatus.PLANNED,
                exercises = exercises,
                setLogs = emptyList(),
                startedAt = null,
                completedAt = null,
                cancelledAt = null,
                pendingEvents = mutableListOf(),
            )
        }

        fun restore(
            id: SessionId,
            templateId: TemplateId?,
            status: SessionStatus,
            exercises: List<SessionExercise>,
            setLogs: List<SetLog>,
            startedAt: Instant?,
            completedAt: Instant?,
            cancelledAt: Instant?,
        ): WorkoutSession = WorkoutSession(
            id = id,
            templateId = templateId,
            status = status,
            exercises = exercises,
            setLogs = setLogs,
            startedAt = startedAt,
            completedAt = completedAt,
            cancelledAt = cancelledAt,
            pendingEvents = mutableListOf(),
        )
    }

    private fun ensureMutable() {
        if (WorkoutSessionStateMachine.isTerminal(status)) {
            throw ImmutableRecordException("Completed or cancelled sessions cannot be modified")
        }
    }

    private fun ensureInProgress() {
        if (status != SessionStatus.IN_PROGRESS) {
            throw ImmutableRecordException("Operation requires session in progress")
        }
    }

    private fun copy(
        status: SessionStatus = this.status,
        setLogs: List<SetLog> = this.setLogs,
        startedAt: Instant? = this.startedAt,
        completedAt: Instant? = this.completedAt,
        cancelledAt: Instant? = this.cancelledAt,
    ): WorkoutSession = WorkoutSession(
        id = id,
        templateId = templateId,
        status = status,
        exercises = exercises,
        setLogs = setLogs,
        startedAt = startedAt,
        completedAt = completedAt,
        cancelledAt = cancelledAt,
        pendingEvents = pendingEvents.toMutableList(),
    )
}
