package com.openfitness.domain.model

import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight

data class TemplateExercise(
    val exerciseId: ExerciseId,
    val order: Int,
    val targetSets: Int,
    val targetReps: RepCount? = null,
    val targetWeight: Weight? = null,
) {
    init {
        require(order >= 0) { "Order must be non-negative" }
        require(targetSets >= 1) { "Target sets must be at least 1" }
    }
}
