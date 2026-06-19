package com.openfitness.domain.valueobject

import java.util.UUID

@JvmInline
value class ExerciseId(val value: UUID) {
    init {
        require(value.version() == 4) { "ExerciseId must be UUID v4" }
    }

    override fun toString(): String = value.toString()

    companion object {
        fun generate(): ExerciseId = ExerciseId(UUID.randomUUID())

        fun fromString(raw: String): ExerciseId = ExerciseId(UUID.fromString(raw.trim()))
    }
}
