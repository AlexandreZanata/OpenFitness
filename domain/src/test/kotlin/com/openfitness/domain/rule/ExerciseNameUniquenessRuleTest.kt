package com.openfitness.domain.rule

import com.openfitness.domain.exception.DuplicateExerciseNameException
import org.junit.jupiter.api.Assertions.assertDoesNotThrow
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class ExerciseNameUniquenessRuleTest {

    private val rule = ExerciseNameUniquenessRule()

    @Test
    fun `GIVEN no exercise named curl WHEN create Curl THEN accepted`() {
        assertDoesNotThrow {
            rule.validate("Curl", emptyList())
        }
    }

    @Test
    fun `GIVEN custom Curl exists WHEN create curl THEN DuplicateExerciseNameException`() {
        assertThrows(DuplicateExerciseNameException::class.java) {
            rule.validate("curl", listOf("Curl"))
        }
    }
}
