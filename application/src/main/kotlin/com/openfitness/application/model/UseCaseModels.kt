package com.openfitness.application.model

import com.openfitness.domain.model.PersonalRecord
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.valueobject.ExerciseId

data class TemplateExerciseInput(
    val exerciseId: ExerciseId,
    val targetSets: Int,
    val targetReps: Int? = null,
    val targetWeightKg: Double? = null,
)

data class CompletionSummary(
    val session: WorkoutSession,
    val newPersonalRecords: List<PersonalRecord>,
)
