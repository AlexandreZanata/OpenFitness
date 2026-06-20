package com.openfitness.app.feature.templates

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.model.TemplateExerciseInput
import com.openfitness.application.usecase.bootstrap.SeedCatalogUseCase
import com.openfitness.application.usecase.exerciselibrary.BrowseExercisesUseCase
import com.openfitness.application.usecase.session.StartWorkoutSessionUseCase
import com.openfitness.application.usecase.template.CreateWorkoutTemplateUseCase
import com.openfitness.application.usecase.template.ListWorkoutTemplatesUseCase
import com.openfitness.application.usecase.template.UpdateWorkoutTemplateUseCase
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.TemplateId
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class TemplatesViewModel @Inject constructor(
    private val seedCatalogUseCase: SeedCatalogUseCase,
    private val listWorkoutTemplatesUseCase: ListWorkoutTemplatesUseCase,
    private val createWorkoutTemplateUseCase: CreateWorkoutTemplateUseCase,
    private val updateWorkoutTemplateUseCase: UpdateWorkoutTemplateUseCase,
    private val startWorkoutSessionUseCase: StartWorkoutSessionUseCase,
    private val browseExercisesUseCase: BrowseExercisesUseCase,
) : ViewModel() {

    private val _uiState = MutableStateFlow(TemplatesUiState())
    val uiState: StateFlow<TemplatesUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            seedCatalogUseCase()
            browseExercisesUseCase("", null)
                .catch { /* ignore for template picker fallback */ }
                .collect { exercises ->
                    _uiState.update {
                        it.copy(
                            availableExercises = exercises.map { ex -> ex.id to ex.name },
                        )
                    }
                }
        }
        viewModelScope.launch {
            listWorkoutTemplatesUseCase()
                .catch {
                    _uiState.update { state ->
                        state.copy(isLoading = false, error = AppError.StorageError)
                    }
                }
                .collect { templates ->
                    _uiState.update { state ->
                        state.copy(
                            templates = templates.map { template ->
                                TemplateUiModel(
                                    id = template.id,
                                    name = template.name,
                                    exerciseCount = template.exercises.size,
                                )
                            },
                            isLoading = false,
                            isEmpty = templates.isEmpty(),
                            error = null,
                        )
                    }
                }
        }
    }

    fun onEvent(event: TemplatesEvent) {
        when (event) {
            TemplatesEvent.ShowCreateDialog -> _uiState.update { it.copy(showCreateDialog = true) }
            TemplatesEvent.DismissCreateDialog -> _uiState.update { it.copy(showCreateDialog = false) }
            is TemplatesEvent.CreateTemplate -> createTemplate(event)
            is TemplatesEvent.ShowEditDialog -> _uiState.update {
                it.copy(showEditDialog = true, editingTemplateId = event.templateId)
            }
            TemplatesEvent.DismissEditDialog -> _uiState.update {
                it.copy(showEditDialog = false, editingTemplateId = null)
            }
            is TemplatesEvent.UpdateTemplate -> updateTemplate(event)
            is TemplatesEvent.StartWorkout -> startWorkout(event)
            TemplatesEvent.Retry -> _uiState.update { it.copy(isLoading = true, error = null) }
        }
    }

    fun onNavigationConsumed() {
        _uiState.update { it.copy(navigateToSessionId = null) }
    }

    private fun createTemplate(event: TemplatesEvent.CreateTemplate) {
        viewModelScope.launch {
            val input = listOf(TemplateExerciseInput(event.exerciseId, targetSets = 3))
            when (val result = createWorkoutTemplateUseCase(event.name, input)) {
                is UseCaseResult.Success -> _uiState.update { it.copy(showCreateDialog = false, error = null) }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }

    private fun updateTemplate(event: TemplatesEvent.UpdateTemplate) {
        viewModelScope.launch {
            when (val result = updateWorkoutTemplateUseCase(event.templateId, event.name, null)) {
                is UseCaseResult.Success -> _uiState.update {
                    it.copy(showEditDialog = false, editingTemplateId = null, error = null)
                }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }

    private fun startWorkout(event: TemplatesEvent.StartWorkout) {
        viewModelScope.launch {
            when (val result = startWorkoutSessionUseCase(event.templateId, event.exerciseIds)) {
                is UseCaseResult.Success -> _uiState.update {
                    it.copy(navigateToSessionId = result.value.id, error = null)
                }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }
}
