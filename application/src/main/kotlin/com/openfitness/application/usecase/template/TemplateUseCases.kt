package com.openfitness.application.usecase.template

import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.error.runUseCase
import com.openfitness.application.model.TemplateExerciseInput
import com.openfitness.domain.exception.RecordNotFoundException
import com.openfitness.domain.model.TemplateExercise
import com.openfitness.domain.model.WorkoutTemplate
import com.openfitness.domain.repository.WorkoutTemplateRepository
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.TemplateId
import com.openfitness.domain.valueobject.Weight
import java.time.Instant

class CreateWorkoutTemplateUseCase(
    private val repo: WorkoutTemplateRepository,
) {
    suspend operator fun invoke(
        name: String,
        exercises: List<TemplateExerciseInput>,
    ): UseCaseResult<WorkoutTemplate> = runUseCase {
        val template = WorkoutTemplate.create(name, exercises.toTemplateExercises())
        repo.save(template)
        template
    }
}

class UpdateWorkoutTemplateUseCase(
    private val repo: WorkoutTemplateRepository,
) {
    suspend operator fun invoke(
        templateId: TemplateId,
        name: String?,
        exercises: List<TemplateExerciseInput>?,
    ): UseCaseResult<WorkoutTemplate> = runUseCase {
        val existing = repo.findById(templateId)
            ?: throw RecordNotFoundException(templateId.toString())
        val now = Instant.now()
        val renamed = if (name != null) existing.rename(name, now) else existing
        val updated = if (exercises != null) {
            WorkoutTemplate.restore(
                id = renamed.id,
                name = renamed.name,
                exercises = exercises.toTemplateExercises(),
                createdAt = renamed.createdAt,
                updatedAt = now,
            )
        } else {
            renamed
        }
        repo.save(updated)
        updated
    }
}

private fun List<TemplateExerciseInput>.toTemplateExercises(): List<TemplateExercise> =
    mapIndexed { index, input ->
        TemplateExercise(
            exerciseId = input.exerciseId,
            order = index,
            targetSets = input.targetSets,
            targetReps = input.targetReps?.let { RepCount(it) },
            targetWeight = input.targetWeightKg?.let { Weight.fromKilograms(it) },
        )
    }
