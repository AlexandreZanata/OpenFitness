package com.openfitness.data.repository

import com.openfitness.data.preferences.UserPreferencesDataStore
import com.openfitness.domain.repository.UserPreferencesRepository
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow

@Singleton
class UserPreferencesRepositoryImpl @Inject constructor(
    private val preferences: UserPreferencesDataStore,
) : UserPreferencesRepository {

    override fun observeRestTimerSeconds(): Flow<Int> = preferences.restTimerSeconds

    override fun observeWeightUnitDisplay(): Flow<String> = preferences.weightUnitDisplay
}
