package com.openfitness.app.feature.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.usecase.session.CorrectCompletedSetUseCase
import com.openfitness.application.usecase.session.GetWorkoutSessionUseCase
import com.openfitness.application.usecase.history.ViewWorkoutHistoryUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class HistoryViewModel @Inject constructor(
    private val viewWorkoutHistoryUseCase: ViewWorkoutHistoryUseCase,
    private val getWorkoutSessionUseCase: GetWorkoutSessionUseCase,
    private val correctCompletedSetUseCase: CorrectCompletedSetUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(HistoryUiState())
    val uiState: StateFlow<HistoryUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            viewWorkoutHistoryUseCase()
                .catch {
                    _uiState.update { state ->
                        state.copy(isLoading = false, error = AppError.StorageError)
                    }
                }
                .collect { sessions ->
                    val models = sessions.map { session ->
                        HistorySessionUiModel(
                            id = session.id,
                            completedAt = session.completedAt,
                            totalSets = session.setLogs.size,
                        )
                    }
                    val lastLabel = models.firstOrNull()?.completedAt?.let { instant ->
                        DateTimeFormatter.ISO_LOCAL_DATE.format(instant.atZone(java.time.ZoneId.systemDefault()))
                    }
                    _uiState.update { state ->
                        state.copy(
                            sessions = models,
                            lastWorkoutLabel = lastLabel,
                            isLoading = false,
                            isEmpty = models.isEmpty(),
                            error = null,
                        )
                    }
                }
        }
    }

    fun onEvent(event: HistoryEvent) {
        when (event) {
            HistoryEvent.Retry -> _uiState.update { it.copy(isLoading = true, error = null) }
            is HistoryEvent.SelectSession -> _uiState.update { it.copy(selectedSessionId = event.sessionId) }
            HistoryEvent.DismissDetail -> _uiState.update { it.copy(selectedSessionId = null) }
            is HistoryEvent.ShowCorrectDialog -> _uiState.update {
                it.copy(showCorrectDialog = true, correctingSetLogId = event.setLogId)
            }
            HistoryEvent.DismissCorrectDialog -> _uiState.update {
                it.copy(showCorrectDialog = false, correctingSetLogId = null)
            }
            is HistoryEvent.ConfirmCorrection -> correctSet(event)
        }
    }

    private fun correctSet(event: HistoryEvent.ConfirmCorrection) {
        val sessionId = _uiState.value.selectedSessionId ?: return
        val setLogId = _uiState.value.correctingSetLogId ?: return
        viewModelScope.launch {
            when (
                val result = correctCompletedSetUseCase(
                    sessionId = sessionId,
                    originalSetLogId = setLogId,
                    weightKg = event.weight.toDoubleOrNull(),
                    reps = event.reps.toIntOrNull(),
                    reason = event.reason,
                )
            ) {
                is UseCaseResult.Success -> _uiState.update {
                    it.copy(showCorrectDialog = false, correctingSetLogId = null, error = null)
                }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }
}
