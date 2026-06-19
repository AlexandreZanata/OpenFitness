package com.openfitness.app.feature.personalrecords

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openfitness.application.error.AppError
import com.openfitness.application.usecase.history.ViewPersonalRecordsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class PersonalRecordsViewModel @Inject constructor(
    private val viewPersonalRecordsUseCase: ViewPersonalRecordsUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(PersonalRecordsUiState())
    val uiState: StateFlow<PersonalRecordsUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            viewPersonalRecordsUseCase()
                .catch {
                    _uiState.update { state ->
                        state.copy(isLoading = false, error = AppError.StorageError)
                    }
                }
                .collect { records ->
                    _uiState.update { state ->
                        state.copy(
                            records = records.map { record ->
                                PersonalRecordUiModel(
                                    exerciseId = record.exerciseId,
                                    metric = record.metric,
                                    value = record.value,
                                )
                            },
                            isLoading = false,
                            isEmpty = records.isEmpty(),
                            error = null,
                        )
                    }
                }
        }
    }

    fun onEvent(event: PersonalRecordsEvent) {
        if (event is PersonalRecordsEvent.Retry) {
            _uiState.update { it.copy(isLoading = true, error = null) }
        }
    }
}
