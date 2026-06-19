package com.openfitness.domain.event

import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import java.time.Instant
import java.util.UUID

data class PersonalRecordAchieved(
    override val eventId: UUID,
    override val occurredAt: Instant,
    val exerciseId: ExerciseId,
    val metric: PersonalRecordMetric,
    val previousValue: Double?,
    val newValue: Double,
    val sessionId: SessionId,
    val setLogId: SetLogId,
    val achievedAt: Instant,
) : DomainEvent {
    override val aggregateId: String = "${exerciseId}_${metric.name}"
}
