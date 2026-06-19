package com.openfitness.domain.event

import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import java.time.Instant
import java.util.UUID

data class SetLogUpdated(
    override val eventId: UUID,
    override val occurredAt: Instant,
    val sessionId: SessionId,
    val setLogId: SetLogId,
    val weightKg: Double?,
    val reps: Int?,
) : DomainEvent {
    override val aggregateId: String = sessionId.toString()
}
