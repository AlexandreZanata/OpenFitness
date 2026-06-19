package com.openfitness.domain.event

import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import java.time.Instant
import java.util.UUID

data class SetLogged(
    override val eventId: UUID,
    override val occurredAt: Instant,
    val sessionId: SessionId,
    val setLogId: SetLogId,
    val exerciseId: ExerciseId,
    val setNumber: Int,
    val weightKg: Double?,
    val reps: Int?,
    val completedAt: Instant,
) : DomainEvent {
    override val aggregateId: String = sessionId.toString()
}
