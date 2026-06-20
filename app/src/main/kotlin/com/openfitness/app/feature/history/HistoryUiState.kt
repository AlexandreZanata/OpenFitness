package com.openfitness.app.feature.history

import com.openfitness.application.error.AppError
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import java.time.Instant

data class HistorySessionUiModel(
    val id: SessionId,
    val completedAt: Instant?,
    val totalSets: Int,
)

data class HistoryCorrectionUiModel(
    val weightKg: Double?,
    val reps: Int?,
    val reason: String?,
)

data class HistorySetLogUiModel(
    val id: SetLogId,
    val setNumber: Int,
    val weightKg: Double?,
    val reps: Int?,
    val corrections: List<HistoryCorrectionUiModel>,
)

data class HistorySessionDetailUiModel(
    val id: SessionId,
    val completedAt: Instant?,
    val setLogs: List<HistorySetLogUiModel>,
)

data class HistoryUiState(
    val sessions: List<HistorySessionUiModel> = emptyList(),
    val lastWorkoutLabel: String? = null,
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
    val selectedSessionId: SessionId? = null,
    val selectedSessionDetail: HistorySessionDetailUiModel? = null,
    val isLoadingDetail: Boolean = false,
    val showCorrectDialog: Boolean = false,
    val correctingSetLogId: SetLogId? = null,
    val weightUnit: String = "kg",
)

sealed interface HistoryEvent {
    data object Retry : HistoryEvent
    data class SelectSession(val sessionId: SessionId) : HistoryEvent
    data object DismissDetail : HistoryEvent
    data class ShowCorrectDialog(val setLogId: SetLogId) : HistoryEvent
    data object DismissCorrectDialog : HistoryEvent
    data class ConfirmCorrection(
        val weight: String,
        val reps: String,
        val reason: String,
    ) : HistoryEvent
}
