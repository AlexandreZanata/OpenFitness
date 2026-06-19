package com.openfitness.domain.model

import com.openfitness.domain.exception.DuplicateExerciseNameException
import com.openfitness.domain.rule.ExerciseNameUniquenessRule
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.MuscleGroup
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class ExerciseExtendedTest {

    @Test
    fun `GIVEN unique name WHEN createCustom THEN exercise created`() {
        val exercise = Exercise.createCustom("Bench Press", MuscleGroup.CHEST, EquipmentType.BARBELL) {}
        assertEquals("Bench Press", exercise.name)
        assertEquals(true, exercise.isCustom)
    }

    @Test
    fun `GIVEN duplicate name WHEN createCustom THEN DuplicateExerciseNameException`() {
        val rule = ExerciseNameUniquenessRule()
        assertThrows(DuplicateExerciseNameException::class.java) {
            Exercise.createCustom("Curl", MuscleGroup.BICEPS, EquipmentType.DUMBBELL) {
                rule.validate(it, listOf("curl"))
            }
        }
    }
}
