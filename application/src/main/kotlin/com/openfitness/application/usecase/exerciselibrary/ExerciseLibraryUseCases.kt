package com.openfitness.application.usecase.exerciselibrary

import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.error.runUseCase
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.repository.ExerciseRepository
import com.openfitness.domain.rule.ExerciseNameUniquenessRule
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.MuscleGroup
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class BrowseExercisesUseCase(
    private val repo: ExerciseRepository,
) {
    operator fun invoke(query: String, filter: MuscleGroup?): Flow<List<Exercise>> =
        repo.observeAll().map { exercises ->
            exercises.filter { exercise ->
                (filter == null || exercise.primaryMuscleGroup == filter) &&
                    (query.isBlank() || exercise.name.contains(query.trim(), ignoreCase = true))
            }
        }
}

class CreateCustomExerciseUseCase(
    private val repo: ExerciseRepository,
    private val uniquenessRule: ExerciseNameUniquenessRule,
) {
    suspend operator fun invoke(
        name: String,
        muscleGroup: MuscleGroup,
        equipment: EquipmentType,
    ): UseCaseResult<Exercise> = runUseCase {
        val existingNames = repo.findAllNames()
        val exercise = Exercise.createCustom(name, muscleGroup, equipment) { trimmed ->
            uniquenessRule.validate(trimmed, existingNames)
        }
        repo.save(exercise)
        exercise
    }
}
