package com.openfitness.domain.valueobject

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class WeightTest {

    @Test
    fun `GIVEN positive kg WHEN fromKilograms THEN accepted`() {
        val weight = Weight.fromKilograms(60.0)
        assertEquals(60.0, weight.kilograms)
    }

    @Test
    fun `GIVEN zero kg WHEN fromKilograms THEN fails BR-002`() {
        assertThrows(IllegalArgumentException::class.java) {
            Weight.fromKilograms(0.0)
        }
    }
}
