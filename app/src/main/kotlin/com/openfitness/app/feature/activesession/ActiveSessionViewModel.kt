package com.openfitness.app.feature.activesession

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.usecase.exerciselibrary.GetExerciseUseCase
import com.openfitness.application.usecase.preferences.ObserveRestTimerUseCase
import com.openfitness.application.usecase.preferences.ObserveWeightUnitUseCase
import com.openfitness.application.usecase.session.CompleteWorkoutSessionUseCase
import com.openfitness.application.usecase.session.EditSetUseCase
import com.openfitness.application.usecase.session.GetWorkoutSessionUseCase
import com.openfitness.application.usecase.session.LogSetUseCase
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.valueobject.SessionId
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class ActiveSessionViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val getWorkoutSessionUseCase: GetWorkoutSessionUseCase,
    private val getExerciseUseCase: GetExerciseUseCase,
    private val logSetUseCase: LogSetUseCase,
    private val editSetUseCase: EditSetUseCase,
    private val completeWorkoutSessionUseCase: CompleteWorkoutSessionUseCase,
    private val observeRestTimerUseCase: ObserveRestTimerUseCase,
    private val observeWeightUnitUseCase: ObserveWeightUnitUseCase,
) : ViewModel() {

    private val sessionId: SessionId = SessionId.fromString(
        checkNotNull(savedStateHandle.get<String>("sessionId")),
    )

    private val _uiState = MutableStateFlow(ActiveSessionUiState(sessionId = sessionId.toString()))
    val uiState: StateFlow<ActiveSessionUiState> = _uiState.asStateFlow()

    private val _completed = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val completed = _completed.asSharedFlow()

    private var restTimerJob: Job? = null

    init {
        viewModelScope.launch {
            observeWeightUnitUseCase().collect { unit ->
                _uiState.update { it.copy(weightUnit = unit) }
            }
        }
        loadSession()
    }

    fun onEvent(event: ActiveSessionEvent) {
        when (event) {
            is ActiveSessionEvent.WeightChanged -> _uiState.update { it.copy(weightInput = event.value) }
            is ActiveSessionEvent.RepsChanged -> _uiState.update { it.copy(repsInput = event.value) }
            ActiveSessionEvent.LogSet -> logSet()
            ActiveSessionEvent.ShowFinishDialog -> _uiState.update { it.copy(showFinishDialog = true) }
            ActiveSessionEvent.DismissFinishDialog -> _uiState.update { it.copy(showFinishDialog = false) }
            ActiveSessionEvent.ConfirmFinish -> completeSession()
            is ActiveSessionEvent.ShowEditSetDialog -> _uiState.update {
                it.copy(showEditSetDialog = true, editingSetLogId = event.setLogId)
            }
            ActiveSessionEvent.DismissEditSetDialog -> _uiState.update {
                it.copy(showEditSetDialog = false, editingSetLogId = null)
            }
            is ActiveSessionEvent.ConfirmEditSet -> editSet(event)
            ActiveSessionEvent.Retry -> loadSession()
        }
    }

    private fun loadSession() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            val session = getWorkoutSessionUseCase(sessionId)
            if (session == null) {
                _uiState.update { it.copy(isLoading = false, error = AppError.NotFound) }
                return@launch
            }
            mapSession(session)
        }
    }

    private suspend fun mapSession(session: WorkoutSession) {
        val exercises = session.exercises.map { exercise ->
            val name = getExerciseUseCase(exercise.exerciseId)?.name ?: exercise.exerciseId.toString()
            SessionExerciseUiModel(
                exerciseId = exercise.exerciseId,
                name = name,
                completedSets = session.setLogs.count { it.exerciseId == exercise.exerciseId },
            )
        }
        val logs = session.setLogs.map { log ->
            SetLogUiModel(
                id = log.id,
                setNumber = log.setNumber,
                weightKg = log.weight?.kilograms,
                reps = log.reps?.value,
            )
        }
        _uiState.update {
            it.copy(
                exercises = exercises,
                setLogs = logs,
                isLoading = false,
                error = null,
            )
        }
    }

    private fun logSet() {
        val state = _uiState.value
        val exercise = state.exercises.getOrNull(state.currentExerciseIndex) ?: return
        val weight = state.weightInput.toDoubleOrNull()
        val reps = state.repsInput.toIntOrNull()
        viewModelScope.launch {
            when (val result = logSetUseCase(sessionId, exercise.exerciseId, weight, reps)) {
                is UseCaseResult.Success -> {
                    getWorkoutSessionUseCase(sessionId)?.let { mapSession(it) }
                    _uiState.update { it.copy(weightInput = "", repsInput = "", error = null) }
                    startRestTimer()
                }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }

    private fun editSet(event: ActiveSessionEvent.ConfirmEditSet) {
        val setLogId = _uiState.value.editingSetLogId ?: return
        viewModelScope.launch {
            when (
                val result = editSetUseCase(
                    sessionId,
                    setLogId,
                    event.weight.toDoubleOrNull(),
                    event.reps.toIntOrNull(),
                )
            ) {
                is UseCaseResult.Success -> {
                    getWorkoutSessionUseCase(sessionId)?.let { mapSession(it) }
                    _uiState.update {
                        it.copy(showEditSetDialog = false, editingSetLogId = null, error = null)
                    }
                }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }

    private fun completeSession() {
        viewModelScope.launch {
            when (val result = completeWorkoutSessionUseCase(sessionId)) {
                is UseCaseResult.Success -> {
                    _uiState.update {
                        it.copy(
                            showFinishDialog = false,
                            isCompleted = true,
                            newPrCount = result.value.newPersonalRecords.size,
                            error = null,
                        )
                    }
                    _completed.tryEmit(Unit)
                }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }

    private fun startRestTimer() {
        restTimerJob?.cancel()
        restTimerJob = viewModelScope.launch {
            val seconds = observeRestTimerUseCase().first()
            _uiState.update { it.copy(restTimerSecondsRemaining = seconds) }
            repeat(seconds) {
                delay(1_000)
                _uiState.update { state ->
                    val remaining = (state.restTimerSecondsRemaining ?: 0) - 1
                    state.copy(restTimerSecondsRemaining = remaining.takeIf { value -> value > 0 })
                }
            }
        }
    }
}
