package com.openfitness.app.feature.activesession

import com.openfitness.application.error.AppError
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.SetLogId

data class SessionExerciseUiModel(
    val exerciseId: ExerciseId,
    val name: String,
    val completedSets: Int,
)

data class SetLogUiModel(
    val id: SetLogId,
    val setNumber: Int,
    val weightKg: Double?,
    val reps: Int?,
)

data class ActiveSessionUiState(
    val sessionId: String? = null,
    val exercises: List<SessionExerciseUiModel> = emptyList(),
    val currentExerciseIndex: Int = 0,
    val setLogs: List<SetLogUiModel> = emptyList(),
    val weightInput: String = "",
    val repsInput: String = "",
    val restTimerSecondsRemaining: Int? = null,
    val isLoading: Boolean = true,
    val error: AppError? = null,
    val showFinishDialog: Boolean = false,
    val showEditSetDialog: Boolean = false,
    val editingSetLogId: SetLogId? = null,
    val isCompleted: Boolean = false,
    val newPrCount: Int = 0,
)

sealed interface ActiveSessionEvent {
    data class WeightChanged(val value: String) : ActiveSessionEvent
    data class RepsChanged(val value: String) : ActiveSessionEvent
    data object LogSet : ActiveSessionEvent
    data object ShowFinishDialog : ActiveSessionEvent
    data object DismissFinishDialog : ActiveSessionEvent
    data object ConfirmFinish : ActiveSessionEvent
    data class ShowEditSetDialog(val setLogId: SetLogId) : ActiveSessionEvent
    data object DismissEditSetDialog : ActiveSessionEvent
    data class ConfirmEditSet(val weight: String, val reps: String) : ActiveSessionEvent
    data object Retry : ActiveSessionEvent
}
