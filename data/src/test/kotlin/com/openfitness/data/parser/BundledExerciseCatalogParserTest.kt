package com.openfitness.data.parser

import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.MuscleGroup
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Test

class BundledExerciseCatalogParserTest {

    private val parser = BundledExerciseCatalogParser()

    @Test
    fun `GIVEN catalog json WHEN parse THEN bundled exercises`() {
        val json = """
            [
              {"name":"Bench Press","primaryMuscleGroup":"CHEST","equipmentType":"BARBELL"}
            ]
        """.trimIndent()
        val exercises = parser.parse(json)
        assertEquals(1, exercises.size)
        assertEquals("Bench Press", exercises.first().name)
        assertEquals(MuscleGroup.CHEST, exercises.first().primaryMuscleGroup)
        assertEquals(EquipmentType.BARBELL, exercises.first().equipmentType)
        assertFalse(exercises.first().isCustom)
    }
}
