package com.openfitness.domain.valueobject

import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class RepCountTest {

    @Test
    fun `GIVEN zero reps WHEN create THEN fails BR-002`() {
        assertThrows(IllegalArgumentException::class.java) {
            RepCount(0)
        }
    }

    @Test
    fun `GIVEN valid reps WHEN create THEN accepted`() {
        RepCount(8)
    }
}
