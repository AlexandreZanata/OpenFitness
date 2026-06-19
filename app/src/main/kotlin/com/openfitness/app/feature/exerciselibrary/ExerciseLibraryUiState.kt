package com.openfitness.app.feature.exerciselibrary

import com.openfitness.application.error.AppError
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup

data class ExerciseUiModel(
    val id: ExerciseId,
    val name: String,
    val muscleGroup: MuscleGroup,
    val equipment: EquipmentType,
    val isCustom: Boolean,
)

data class ExerciseLibraryUiState(
    val exercises: List<ExerciseUiModel> = emptyList(),
    val searchQuery: String = "",
    val selectedFilter: MuscleGroup? = null,
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
    val showAddDialog: Boolean = false,
    val showEditDialog: Boolean = false,
    val editingExerciseId: ExerciseId? = null,
)

sealed interface ExerciseLibraryEvent {
    data class SearchChanged(val query: String) : ExerciseLibraryEvent
    data class FilterChanged(val filter: MuscleGroup?) : ExerciseLibraryEvent
    data object ShowAddDialog : ExerciseLibraryEvent
    data object DismissAddDialog : ExerciseLibraryEvent
    data class CreateCustom(
        val name: String,
        val muscleGroup: MuscleGroup,
        val equipment: EquipmentType,
    ) : ExerciseLibraryEvent
    data class ShowEditDialog(val exerciseId: ExerciseId) : ExerciseLibraryEvent
    data object DismissEditDialog : ExerciseLibraryEvent
    data class UpdateCustom(
        val exerciseId: ExerciseId,
        val name: String,
        val muscleGroup: MuscleGroup,
        val equipment: EquipmentType,
    ) : ExerciseLibraryEvent
    data object Retry : ExerciseLibraryEvent
}
