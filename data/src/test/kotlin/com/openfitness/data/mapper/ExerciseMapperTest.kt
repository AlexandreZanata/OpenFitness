package com.openfitness.data.mapper

import com.openfitness.data.local.entity.ExerciseEntity
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import java.time.Instant

class ExerciseMapperTest {

    @Test
    fun `round trip exercise entity`() {
        val exercise = Exercise.restore(
            id = ExerciseId.generate(),
            name = "Row",
            primaryMuscleGroup = MuscleGroup.BACK,
            equipmentType = EquipmentType.CABLE,
            isCustom = true,
            createdAt = Instant.parse("2026-06-19T10:00:00Z"),
        )
        val entity = ExerciseMapper.toEntity(exercise)
        val restored = ExerciseMapper.toDomain(entity)
        assertEquals(exercise.id, restored.id)
        assertEquals(exercise.name, restored.name)
        assertEquals(exercise.isCustom, restored.isCustom)
    }

    @Test
    fun `entity fields map to schema columns`() {
        val entity = ExerciseEntity(
            id = "550e8400-e29b-41d4-a716-446655440000",
            name = "Squat",
            primaryMuscleGroup = "LEGS",
            equipmentType = "BARBELL",
            isCustom = false,
            createdAt = 1L,
        )
        val domain = ExerciseMapper.toDomain(entity)
        assertEquals(MuscleGroup.LEGS, domain.primaryMuscleGroup)
    }
}
