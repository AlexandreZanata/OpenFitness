package com.openfitness.domain.model

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.rule.BundledExerciseImmutabilityRule
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import java.time.Instant

class Exercise private constructor(
    val id: ExerciseId,
    val name: String,
    val primaryMuscleGroup: MuscleGroup,
    val equipmentType: EquipmentType,
    val isCustom: Boolean,
    val createdAt: Instant,
) {
    fun updateCustom(
        name: String,
        muscleGroup: MuscleGroup,
        equipment: EquipmentType,
        uniquenessRule: (String) -> Unit,
        immutabilityRule: BundledExerciseImmutabilityRule = BundledExerciseImmutabilityRule(),
    ): Exercise {
        immutabilityRule.validateMutation(isCustom)
        val trimmed = validateName(name)
        uniquenessRule(trimmed)
        return Exercise(
            id = id,
            name = trimmed,
            primaryMuscleGroup = muscleGroup,
            equipmentType = equipment,
            isCustom = true,
            createdAt = createdAt,
        )
    }

    companion object {
        fun createCustom(
            name: String,
            muscleGroup: MuscleGroup,
            equipment: EquipmentType,
            createdAt: Instant = Instant.now(),
            uniquenessRule: (String) -> Unit,
        ): Exercise {
            val trimmed = validateName(name)
            uniquenessRule(trimmed)
            return Exercise(
                id = ExerciseId.generate(),
                name = trimmed,
                primaryMuscleGroup = muscleGroup,
                equipmentType = equipment,
                isCustom = true,
                createdAt = createdAt,
            )
        }

        fun restore(
            id: ExerciseId,
            name: String,
            primaryMuscleGroup: MuscleGroup,
            equipmentType: EquipmentType,
            isCustom: Boolean,
            createdAt: Instant,
        ): Exercise = Exercise(
            id = id,
            name = validateName(name),
            primaryMuscleGroup = primaryMuscleGroup,
            equipmentType = equipmentType,
            isCustom = isCustom,
            createdAt = createdAt,
        )

        fun rename(
            exercise: Exercise,
            newName: String,
            uniquenessRule: (String) -> Unit,
        ): Exercise {
            BundledExerciseImmutabilityRule().validateMutation(exercise.isCustom)
            return exercise.updateCustom(
                name = newName,
                muscleGroup = exercise.primaryMuscleGroup,
                equipment = exercise.equipmentType,
                uniquenessRule = uniquenessRule,
            )
        }

        private fun validateName(name: String): String {
            val trimmed = name.trim()
            if (trimmed.length !in 2..80) {
                throw DomainException("Exercise name must be between 2 and 80 characters")
            }
            return trimmed
        }
    }
}
