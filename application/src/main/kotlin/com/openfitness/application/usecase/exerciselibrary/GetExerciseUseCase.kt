package com.openfitness.application.usecase.exerciselibrary

import com.openfitness.domain.model.Exercise
import com.openfitness.domain.repository.ExerciseRepository
import com.openfitness.domain.valueobject.ExerciseId

class GetExerciseUseCase(
    private val repo: ExerciseRepository,
) {
    suspend operator fun invoke(id: ExerciseId): Exercise? = repo.findById(id)
}
