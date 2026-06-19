package com.openfitness.application.usecase.exerciselibrary

import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.error.runUseCase
import com.openfitness.domain.exception.RecordNotFoundException
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.repository.ExerciseRepository
import com.openfitness.domain.rule.ExerciseNameUniquenessRule
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup

class UpdateCustomExerciseUseCase(
    private val repo: ExerciseRepository,
    private val uniquenessRule: ExerciseNameUniquenessRule,
) {
    suspend operator fun invoke(
        exerciseId: ExerciseId,
        name: String,
        muscleGroup: MuscleGroup,
        equipment: EquipmentType,
    ): UseCaseResult<Exercise> = runUseCase {
        val existing = repo.findById(exerciseId)
            ?: throw RecordNotFoundException(exerciseId.toString())
        val otherNames = repo.findAllNames().filter { it != existing.name }
        val updated = existing.updateCustom(
            name = name,
            muscleGroup = muscleGroup,
            equipment = equipment,
            uniquenessRule = { trimmed -> uniquenessRule.validate(trimmed, otherNames) },
        )
        repo.save(updated)
        updated
    }
}
