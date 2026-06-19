package com.openfitness.domain.model

import com.openfitness.domain.valueobject.ExerciseId

data class SessionExercise(
    val exerciseId: ExerciseId,
    val order: Int,
) {
    init {
        require(order >= 0) { "Order must be non-negative" }
    }
}
