package com.openfitness.data.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.userPreferencesDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "user_preferences",
)

@Singleton
class UserPreferencesDataStore @Inject constructor(
    @ApplicationContext context: Context,
) {
    private val dataStore = context.userPreferencesDataStore

    val restTimerSeconds: Flow<Int> = dataStore.data.map { preferences ->
        preferences[KEY_REST_TIMER_SECONDS] ?: DEFAULT_REST_TIMER_SECONDS
    }

    suspend fun getRestTimerSeconds(): Int = restTimerSeconds.first()

    suspend fun setRestTimerSeconds(seconds: Int) {
        dataStore.edit { preferences ->
            preferences[KEY_REST_TIMER_SECONDS] = seconds
        }
    }

    val weightUnitDisplay: Flow<String> = dataStore.data.map { preferences ->
        preferences[KEY_WEIGHT_UNIT_DISPLAY] ?: DEFAULT_WEIGHT_UNIT_DISPLAY
    }

    suspend fun getWeightUnitDisplay(): String = weightUnitDisplay.first()

    suspend fun setWeightUnitDisplay(unit: String) {
        dataStore.edit { preferences ->
            preferences[KEY_WEIGHT_UNIT_DISPLAY] = unit
        }
    }

    suspend fun isCatalogSeeded(): Boolean = dataStore.data
        .map { preferences -> preferences[KEY_CATALOG_SEEDED] ?: false }
        .first()

    suspend fun setCatalogSeeded(seeded: Boolean) {
        dataStore.edit { preferences ->
            preferences[KEY_CATALOG_SEEDED] = seeded
        }
    }

    companion object {
        const val DEFAULT_REST_TIMER_SECONDS = 90
        const val DEFAULT_WEIGHT_UNIT_DISPLAY = "kg"

        private val KEY_REST_TIMER_SECONDS = intPreferencesKey("rest_timer_seconds")
        private val KEY_WEIGHT_UNIT_DISPLAY = stringPreferencesKey("weight_unit_display")
        private val KEY_CATALOG_SEEDED = booleanPreferencesKey("catalog_seeded")
    }
}
