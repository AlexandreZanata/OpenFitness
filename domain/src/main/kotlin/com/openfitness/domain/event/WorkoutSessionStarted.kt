package com.openfitness.domain.event

import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.TemplateId
import java.time.Instant
import java.util.UUID

data class WorkoutSessionStarted(
    override val eventId: UUID,
    override val occurredAt: Instant,
    val sessionId: SessionId,
    val templateId: TemplateId?,
    val exerciseIds: List<ExerciseId>,
    val startedAt: Instant,
) : DomainEvent {
    override val aggregateId: String = sessionId.toString()
}
