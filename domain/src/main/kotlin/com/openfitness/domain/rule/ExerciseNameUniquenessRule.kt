package com.openfitness.domain.rule

import com.openfitness.domain.exception.DuplicateExerciseNameException

class ExerciseNameUniquenessRule {
    fun validate(name: String, existingNames: List<String>) {
        val normalized = normalize(name)
        val duplicate = existingNames.any { normalize(it) == normalized }
        if (duplicate) {
            throw DuplicateExerciseNameException(name.trim())
        }
    }

    private fun normalize(name: String): String = name.trim().lowercase()
}
