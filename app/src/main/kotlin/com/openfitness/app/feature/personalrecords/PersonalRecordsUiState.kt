package com.openfitness.app.feature.personalrecords

import com.openfitness.application.error.AppError
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric

data class PersonalRecordUiModel(
    val exerciseId: ExerciseId,
    val metric: PersonalRecordMetric,
    val value: Double,
)

data class PersonalRecordsUiState(
    val records: List<PersonalRecordUiModel> = emptyList(),
    val isLoading: Boolean = true,
    val isEmpty: Boolean = false,
    val error: AppError? = null,
)

sealed interface PersonalRecordsEvent {
    data object Retry : PersonalRecordsEvent
}
