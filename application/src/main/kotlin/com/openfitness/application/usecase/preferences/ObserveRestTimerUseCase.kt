package com.openfitness.application.usecase.preferences

import com.openfitness.domain.repository.UserPreferencesRepository
import kotlinx.coroutines.flow.Flow

class ObserveRestTimerUseCase(
    private val preferences: UserPreferencesRepository,
) {
    operator fun invoke(): Flow<Int> = preferences.observeRestTimerSeconds()
}
