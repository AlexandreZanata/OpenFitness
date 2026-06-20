package com.openfitness.app.feature.templates

import com.openfitness.application.error.AppError
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.TemplateId

data class TemplateUiModel(
    val id: TemplateId,
    val name: String,
    val exerciseCount: Int,
)

data class TemplatesUiState(
    val templates: List<TemplateUiModel> = emptyList(),
    val availableExercises: List<Pair<ExerciseId, String>> = emptyList(),
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
    val showCreateDialog: Boolean = false,
    val showEditDialog: Boolean = false,
    val editingTemplateId: TemplateId? = null,
    val navigateToSessionId: SessionId? = null,
)

sealed interface TemplatesEvent {
    data object ShowCreateDialog : TemplatesEvent
    data object DismissCreateDialog : TemplatesEvent
    data class CreateTemplate(val name: String, val exerciseId: ExerciseId) : TemplatesEvent
    data class ShowEditDialog(val templateId: TemplateId) : TemplatesEvent
    data object DismissEditDialog : TemplatesEvent
    data class UpdateTemplate(val templateId: TemplateId, val name: String) : TemplatesEvent
    data class StartWorkout(val exerciseIds: List<ExerciseId>, val templateId: TemplateId?) : TemplatesEvent
    data object Retry : TemplatesEvent
}
