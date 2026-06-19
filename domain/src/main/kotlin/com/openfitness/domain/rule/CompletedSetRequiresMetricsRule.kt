package com.openfitness.domain.rule

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight

class CompletedSetRequiresMetricsRule {
    fun validate(weight: Weight?, reps: RepCount?) {
        if (weight == null && reps == null) {
            throw DomainException("Completed set requires at least weight or reps")
        }
    }
}
