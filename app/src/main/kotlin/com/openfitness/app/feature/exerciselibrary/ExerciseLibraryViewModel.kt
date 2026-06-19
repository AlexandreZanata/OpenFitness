package com.openfitness.app.feature.exerciselibrary

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.usecase.bootstrap.SeedCatalogUseCase
import com.openfitness.application.usecase.exerciselibrary.BrowseExercisesUseCase
import com.openfitness.application.usecase.exerciselibrary.CreateCustomExerciseUseCase
import com.openfitness.application.usecase.exerciselibrary.UpdateCustomExerciseUseCase
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.valueobject.MuscleGroup
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class ExerciseLibraryViewModel @Inject constructor(
    private val seedCatalogUseCase: SeedCatalogUseCase,
    private val browseExercisesUseCase: BrowseExercisesUseCase,
    private val createCustomExerciseUseCase: CreateCustomExerciseUseCase,
    private val updateCustomExerciseUseCase: UpdateCustomExerciseUseCase,
) : ViewModel() {

    private val searchQuery = MutableStateFlow("")
    private val selectedFilter = MutableStateFlow<MuscleGroup?>(null)
    private val _uiState = MutableStateFlow(ExerciseLibraryUiState())
    val uiState: StateFlow<ExerciseLibraryUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch { seedCatalogUseCase() }
        viewModelScope.launch {
            combine(searchQuery, selectedFilter) { query, filter -> query to filter }
                .flatMapLatest { (query, filter) -> browseExercisesUseCase(query, filter) }
                .catch {
                    _uiState.update { state ->
                        state.copy(isLoading = false, error = AppError.StorageError)
                    }
                }
                .collect { exercises ->
                    val models = exercises.map(::toUiModel)
                    _uiState.update { state ->
                        state.copy(
                            exercises = models,
                            searchQuery = searchQuery.value,
                            selectedFilter = selectedFilter.value,
                            isLoading = false,
                            isEmpty = models.isEmpty(),
                            error = null,
                        )
                    }
                }
        }
    }

    fun onEvent(event: ExerciseLibraryEvent) {
        when (event) {
            is ExerciseLibraryEvent.SearchChanged -> searchQuery.value = event.query
            is ExerciseLibraryEvent.FilterChanged -> selectedFilter.value = event.filter
            ExerciseLibraryEvent.ShowAddDialog -> _uiState.update { it.copy(showAddDialog = true) }
            ExerciseLibraryEvent.DismissAddDialog -> _uiState.update { it.copy(showAddDialog = false) }
            is ExerciseLibraryEvent.CreateCustom -> createCustom(event)
            is ExerciseLibraryEvent.ShowEditDialog -> _uiState.update {
                it.copy(showEditDialog = true, editingExerciseId = event.exerciseId)
            }
            ExerciseLibraryEvent.DismissEditDialog -> _uiState.update {
                it.copy(showEditDialog = false, editingExerciseId = null)
            }
            is ExerciseLibraryEvent.UpdateCustom -> updateCustom(event)
            ExerciseLibraryEvent.Retry -> _uiState.update { it.copy(isLoading = true, error = null) }
        }
    }

    private fun createCustom(event: ExerciseLibraryEvent.CreateCustom) {
        viewModelScope.launch {
            when (val result = createCustomExerciseUseCase(event.name, event.muscleGroup, event.equipment)) {
                is UseCaseResult.Success -> _uiState.update { it.copy(showAddDialog = false, error = null) }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }

    private fun updateCustom(event: ExerciseLibraryEvent.UpdateCustom) {
        viewModelScope.launch {
            when (
                val result = updateCustomExerciseUseCase(
                    event.exerciseId,
                    event.name,
                    event.muscleGroup,
                    event.equipment,
                )
            ) {
                is UseCaseResult.Success -> _uiState.update {
                    it.copy(showEditDialog = false, editingExerciseId = null, error = null)
                }
                is UseCaseResult.Failure -> _uiState.update { it.copy(error = result.error) }
            }
        }
    }

    private fun toUiModel(exercise: Exercise) = ExerciseUiModel(
        id = exercise.id,
        name = exercise.name,
        muscleGroup = exercise.primaryMuscleGroup,
        equipment = exercise.equipmentType,
        isCustom = exercise.isCustom,
    )
}
