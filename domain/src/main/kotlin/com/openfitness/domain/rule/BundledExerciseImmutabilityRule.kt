package com.openfitness.domain.rule

import com.openfitness.domain.exception.ImmutableRecordException

class BundledExerciseImmutabilityRule {
    fun validateMutation(isCustom: Boolean) {
        if (!isCustom) {
            throw ImmutableRecordException("Bundled exercises cannot be modified")
        }
    }
}
