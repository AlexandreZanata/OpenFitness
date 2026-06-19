package com.openfitness.domain.model

import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.Weight
import java.time.Instant
import java.util.UUID

/**
 * Append-only correction for a completed session set (BR-009).
 * Never mutates the original [SetLog] row.
 */
data class RecordCorrection(
    val id: String,
    val sessionId: SessionId,
    val originalSetLogId: SetLogId,
    val correctedWeight: Weight?,
    val correctedReps: RepCount?,
    val reason: String?,
    val createdAt: Instant,
) {
    companion object {
        fun create(
            sessionId: SessionId,
            originalSetLogId: SetLogId,
            correctedWeight: Weight?,
            correctedReps: RepCount?,
            reason: String?,
            createdAt: Instant = Instant.now(),
        ): RecordCorrection = RecordCorrection(
            id = UUID.randomUUID().toString(),
            sessionId = sessionId,
            originalSetLogId = originalSetLogId,
            correctedWeight = correctedWeight,
            correctedReps = correctedReps,
            reason = reason?.trim()?.takeIf { it.isNotEmpty() },
            createdAt = createdAt,
        )
    }
}
