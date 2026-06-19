package com.openfitness.domain.rule

import com.openfitness.domain.model.PersonalRecordAggregate
import com.openfitness.domain.model.PersonalRecordCandidate
import com.openfitness.domain.model.PersonalRecordUpdateResult
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.valueobject.PersonalRecordMetric
import java.time.Instant

class PersonalRecordEvaluationRule {
    fun evaluate(
        session: WorkoutSession,
        currentRecords: Map<Pair<String, PersonalRecordMetric>, PersonalRecordAggregate>,
        completedAt: Instant,
    ): List<PersonalRecordUpdateResult> {
        val results = mutableListOf<PersonalRecordUpdateResult>()
        val setsByExercise = session.setLogs.groupBy { it.exerciseId }

        for ((exerciseId, sets) in setsByExercise) {
            val maxWeightSet = sets.filter { it.weight != null }
                .maxByOrNull { it.weight!!.kilograms }
            if (maxWeightSet?.weight != null) {
                val key = exerciseId.toString() to PersonalRecordMetric.MAX_WEIGHT
                val aggregate = currentRecords[key] ?: PersonalRecordAggregate(null)
                val update = aggregate.tryUpdate(
                    PersonalRecordCandidate(
                        exerciseId = exerciseId,
                        metric = PersonalRecordMetric.MAX_WEIGHT,
                        value = maxWeightSet.weight.kilograms,
                        sessionId = session.id,
                        setLogId = maxWeightSet.id,
                        achievedAt = completedAt,
                    ),
                )
                if (update is PersonalRecordUpdateResult.NewRecord) {
                    results.add(update)
                }
            }

            val referenceWeight = maxWeightSet?.weight?.kilograms
            val maxRepsSet = if (referenceWeight != null) {
                sets.filter { it.reps != null && it.weight?.kilograms == referenceWeight }
                    .maxByOrNull { it.reps!!.value }
            } else {
                sets.filter { it.reps != null }.maxByOrNull { it.reps!!.value }
            }
            if (maxRepsSet?.reps != null) {
                val key = exerciseId.toString() to PersonalRecordMetric.MAX_REPS
                val aggregate = currentRecords[key] ?: PersonalRecordAggregate(null)
                val update = aggregate.tryUpdate(
                    PersonalRecordCandidate(
                        exerciseId = exerciseId,
                        metric = PersonalRecordMetric.MAX_REPS,
                        value = maxRepsSet.reps.value.toDouble(),
                        sessionId = session.id,
                        setLogId = maxRepsSet.id,
                        achievedAt = completedAt,
                    ),
                )
                if (update is PersonalRecordUpdateResult.NewRecord) {
                    results.add(update)
                }
            }
        }
        return results
    }

    fun evaluateSetsOnly(sets: List<SetLog>): Boolean = sets.isNotEmpty()
}
