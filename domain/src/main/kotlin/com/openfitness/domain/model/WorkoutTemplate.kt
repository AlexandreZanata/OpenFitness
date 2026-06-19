package com.openfitness.domain.model

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.rule.SessionMustHaveExercisesRule
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.TemplateId
import com.openfitness.domain.valueobject.Weight
import java.time.Instant

class WorkoutTemplate private constructor(
    val id: TemplateId,
    val name: String,
    val exercises: List<TemplateExercise>,
    val createdAt: Instant,
    val updatedAt: Instant,
) {
    fun addExercise(
        exerciseId: ExerciseId,
        targetSets: Int,
        targetReps: RepCount? = null,
        targetWeight: Weight? = null,
        updatedAt: Instant,
    ): WorkoutTemplate {
        ensureNoDuplicate(exerciseId)
        val newExercise = TemplateExercise(
            exerciseId = exerciseId,
            order = exercises.size,
            targetSets = targetSets,
            targetReps = targetReps,
            targetWeight = targetWeight,
        )
        return copyWith(exercises + newExercise, updatedAt)
    }

    fun removeExercise(exerciseId: ExerciseId, updatedAt: Instant): WorkoutTemplate {
        val filtered = exercises.filterNot { it.exerciseId == exerciseId }
        SessionMustHaveExercisesRule().validate(filtered.size)
        return copyWith(reindex(filtered), updatedAt)
    }

    fun rename(newName: String, updatedAt: Instant): WorkoutTemplate =
        copyWith(exercises, updatedAt, name = validateName(newName))

    companion object {
        fun create(
            name: String,
            exercises: List<TemplateExercise>,
            createdAt: Instant = Instant.now(),
        ): WorkoutTemplate {
            SessionMustHaveExercisesRule().validate(exercises.size)
            validateUniqueExercises(exercises)
            validateUniqueOrders(exercises)
            return WorkoutTemplate(
                id = TemplateId.generate(),
                name = validateName(name),
                exercises = exercises,
                createdAt = createdAt,
                updatedAt = createdAt,
            )
        }

        fun restore(
            id: TemplateId,
            name: String,
            exercises: List<TemplateExercise>,
            createdAt: Instant,
            updatedAt: Instant,
        ): WorkoutTemplate {
            SessionMustHaveExercisesRule().validate(exercises.size)
            validateUniqueExercises(exercises)
            return WorkoutTemplate(
                id = id,
                name = validateName(name),
                exercises = exercises,
                createdAt = createdAt,
                updatedAt = updatedAt,
            )
        }

        private fun validateName(name: String): String {
            val trimmed = name.trim()
            if (trimmed.length !in 2..60) {
                throw DomainException("Template name must be between 2 and 60 characters")
            }
            return trimmed
        }

        private fun validateUniqueExercises(exercises: List<TemplateExercise>) {
            val ids = exercises.map { it.exerciseId }
            if (ids.distinct().size != ids.size) {
                throw DomainException("Duplicate exercise in template")
            }
        }

        private fun validateUniqueOrders(exercises: List<TemplateExercise>) {
            val orders = exercises.map { it.order }
            if (orders.distinct().size != orders.size) {
                throw DomainException("Duplicate order index in template")
            }
        }
    }

    private fun ensureNoDuplicate(exerciseId: ExerciseId) {
        if (exercises.any { it.exerciseId == exerciseId }) {
            throw DomainException("Duplicate exercise in template")
        }
    }

    private fun reindex(exercises: List<TemplateExercise>): List<TemplateExercise> =
        exercises.mapIndexed { index, item -> item.copy(order = index) }

    private fun copyWith(
        exercises: List<TemplateExercise>,
        updatedAt: Instant,
        name: String = this.name,
    ): WorkoutTemplate = WorkoutTemplate(
        id = id,
        name = name,
        exercises = exercises,
        createdAt = createdAt,
        updatedAt = updatedAt,
    )
}
