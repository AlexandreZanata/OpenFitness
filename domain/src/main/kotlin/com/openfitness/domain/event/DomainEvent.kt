package com.openfitness.domain.event

import java.time.Instant
import java.util.UUID

interface DomainEvent {
    val eventId: UUID
    val occurredAt: Instant
    val aggregateId: String
}

internal fun newEventId(): UUID = UUID.randomUUID()
