package com.openfitness.domain.model

import com.openfitness.domain.event.PersonalRecordAchieved
import com.openfitness.domain.event.newEventId
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import java.time.Instant

data class PersonalRecord(
    val exerciseId: ExerciseId,
    val metric: PersonalRecordMetric,
    val value: Double,
    val achievedAt: Instant,
    val sessionId: SessionId,
    val setLogId: SetLogId,
) {
    init {
        require(value > 0) { "Personal record value must be positive" }
    }
}

data class PersonalRecordCandidate(
    val exerciseId: ExerciseId,
    val metric: PersonalRecordMetric,
    val value: Double,
    val sessionId: SessionId,
    val setLogId: SetLogId,
    val achievedAt: Instant,
)

sealed class PersonalRecordUpdateResult {
    data object NoChange : PersonalRecordUpdateResult()

    data class NewRecord(
        val record: PersonalRecord,
        val event: PersonalRecordAchieved,
    ) : PersonalRecordUpdateResult()
}

data class PersonalRecordHistoryEntry(
    val id: String,
    val exerciseId: ExerciseId,
    val metric: PersonalRecordMetric,
    val value: Double,
    val achievedAt: Instant,
    val sessionId: SessionId,
    val setLogId: SetLogId,
    val supersededAt: Instant,
)

class PersonalRecordAggregate(
    val current: PersonalRecord?,
) {
    fun tryUpdate(candidate: PersonalRecordCandidate): PersonalRecordUpdateResult {
        if (candidate.value <= 0) {
            return PersonalRecordUpdateResult.NoChange
        }
        val previous = current?.value
        if (previous != null && candidate.value <= previous) {
            return PersonalRecordUpdateResult.NoChange
        }
        val record = PersonalRecord(
            exerciseId = candidate.exerciseId,
            metric = candidate.metric,
            value = candidate.value,
            achievedAt = candidate.achievedAt,
            sessionId = candidate.sessionId,
            setLogId = candidate.setLogId,
        )
        val event = PersonalRecordAchieved(
            eventId = newEventId(),
            occurredAt = candidate.achievedAt,
            exerciseId = candidate.exerciseId,
            metric = candidate.metric,
            previousValue = previous,
            newValue = candidate.value,
            sessionId = candidate.sessionId,
            setLogId = candidate.setLogId,
            achievedAt = candidate.achievedAt,
        )
        return PersonalRecordUpdateResult.NewRecord(record, event)
    }
}
