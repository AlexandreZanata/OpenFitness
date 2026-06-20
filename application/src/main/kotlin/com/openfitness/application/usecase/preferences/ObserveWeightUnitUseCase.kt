package com.openfitness.application.usecase.preferences

import com.openfitness.domain.repository.UserPreferencesRepository
import kotlinx.coroutines.flow.Flow

class ObserveWeightUnitUseCase(
    private val preferences: UserPreferencesRepository,
) {
    operator fun invoke(): Flow<String> = preferences.observeWeightUnitDisplay()
}
