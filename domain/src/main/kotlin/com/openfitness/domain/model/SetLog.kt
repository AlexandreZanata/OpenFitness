package com.openfitness.domain.model

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.rule.CompletedSetRequiresMetricsRule
import com.openfitness.domain.rule.PositiveSetValuesRule
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.Weight
import java.time.Instant

data class SetLog(
    val id: SetLogId,
    val sessionId: SessionId,
    val exerciseId: ExerciseId,
    val setNumber: Int,
    val weight: Weight?,
    val reps: RepCount?,
    val completedAt: Instant,
) {
    init {
        require(setNumber >= 1) { "Set number must be at least 1" }
        CompletedSetRequiresMetricsRule().validate(weight, reps)
    }

    fun withMetrics(weight: Weight?, reps: RepCount?, updatedAt: Instant): SetLog {
        PositiveSetValuesRule().validate(weight, reps)
        CompletedSetRequiresMetricsRule().validate(weight, reps)
        return copy(
            weight = weight,
            reps = reps,
            completedAt = updatedAt,
        )
    }

    companion object {
        fun create(
            sessionId: SessionId,
            exerciseId: ExerciseId,
            setNumber: Int,
            weight: Weight?,
            reps: RepCount?,
            completedAt: Instant,
        ): SetLog {
            if (setNumber < 1) {
                throw DomainException("Set number must be at least 1")
            }
            PositiveSetValuesRule().validate(weight, reps)
            CompletedSetRequiresMetricsRule().validate(weight, reps)
            return SetLog(
                id = SetLogId.generate(),
                sessionId = sessionId,
                exerciseId = exerciseId,
                setNumber = setNumber,
                weight = weight,
                reps = reps,
                completedAt = completedAt,
            )
        }
    }
}
