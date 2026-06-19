package com.openfitness.domain.valueobject

import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class ValueObjectValidationTest {

    @Test
    fun `GIVEN negative duration WHEN create THEN fails`() {
        assertThrows(IllegalArgumentException::class.java) {
            Duration(-1)
        }
    }

    @Test
    fun `GIVEN invalid exercise id WHEN fromString THEN fails`() {
        assertThrows(IllegalArgumentException::class.java) {
            ExerciseId.fromString("not-a-uuid")
        }
    }

    @Test
    fun `GIVEN invalid template id WHEN fromString THEN fails`() {
        assertThrows(IllegalArgumentException::class.java) {
            TemplateId.fromString("bad")
        }
    }
}
