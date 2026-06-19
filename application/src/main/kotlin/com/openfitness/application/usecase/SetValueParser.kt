package com.openfitness.application.usecase

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight

internal fun parseWeight(weightKg: Double?): Weight? =
    try {
        weightKg?.let { Weight.fromKilograms(it) }
    } catch (_: IllegalArgumentException) {
        throw DomainException("Invalid weight")
    }

internal fun parseReps(reps: Int?): RepCount? =
    try {
        reps?.let { RepCount(it) }
    } catch (_: IllegalArgumentException) {
        throw DomainException("Invalid reps")
    }
