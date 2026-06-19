package com.openfitness.domain.event

import com.openfitness.domain.valueobject.SessionId
import java.time.Instant
import java.util.UUID

data class WorkoutSessionCompleted(
    override val eventId: UUID,
    override val occurredAt: Instant,
    val sessionId: SessionId,
    val completedAt: Instant,
    val totalSets: Int,
    val durationSeconds: Long,
) : DomainEvent {
    override val aggregateId: String = sessionId.toString()
}
