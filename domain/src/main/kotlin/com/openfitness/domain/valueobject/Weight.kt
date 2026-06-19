package com.openfitness.domain.valueobject

@JvmInline
value class Weight(val kilograms: Double) {
    init {
        require(kilograms > 0) { "Weight must be positive" }
    }

    companion object {
        fun fromKilograms(kg: Double): Weight = Weight(
            (kotlin.math.round(kg * 100) / 100.0),
        )
    }
}
