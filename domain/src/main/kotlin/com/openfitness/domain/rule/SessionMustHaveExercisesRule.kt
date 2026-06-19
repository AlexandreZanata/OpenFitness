package com.openfitness.domain.rule

import com.openfitness.domain.exception.DomainException

class SessionMustHaveExercisesRule {
    fun validate(exerciseCount: Int) {
        if (exerciseCount < 1) {
            throw DomainException("Session must contain at least one exercise")
        }
    }
}
