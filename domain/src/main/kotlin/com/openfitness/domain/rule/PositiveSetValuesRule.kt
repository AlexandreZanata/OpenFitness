package com.openfitness.domain.rule

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight

class PositiveSetValuesRule {
    fun validate(weight: Weight?, reps: RepCount?) {
        // Value objects already enforce positivity; this rule documents BR-002 orchestration.
        if (weight == null && reps == null) {
            throw DomainException("Set must have weight and/or reps")
        }
    }
}
