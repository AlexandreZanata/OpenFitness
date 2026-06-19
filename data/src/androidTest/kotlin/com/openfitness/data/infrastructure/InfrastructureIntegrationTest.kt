package com.openfitness.data.infrastructure

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.openfitness.data.local.OpenFitnessDatabase
import com.openfitness.data.mapper.SetLogMapper
import com.openfitness.data.mapper.WorkoutSessionMapper
import com.openfitness.data.parser.BundledExerciseCatalogParser
import com.openfitness.data.preferences.UserPreferencesDataStore
import com.openfitness.data.repository.CatalogSeederImpl
import com.openfitness.data.transaction.RoomTransactionRunner
import com.openfitness.domain.model.SessionExercise
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight
import java.time.Instant
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class InfrastructureIntegrationTest {

    private lateinit var context: Context
    private lateinit var database: OpenFitnessDatabase
    private lateinit var preferences: UserPreferencesDataStore
    private lateinit var transactionRunner: RoomTransactionRunner
    private lateinit var catalogSeeder: CatalogSeederImpl

    @Before
    fun setup() {
        context = ApplicationProvider.getApplicationContext()
        database = Room.inMemoryDatabaseBuilder(context, OpenFitnessDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        preferences = UserPreferencesDataStore(context)
        transactionRunner = RoomTransactionRunner(database)
        catalogSeeder = CatalogSeederImpl(
            context,
            database.exerciseDao(),
            BundledExerciseCatalogParser(),
            preferences,
        )
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun rest_timer_preference_round_trip() = runBlocking {
        assertEquals(
            UserPreferencesDataStore.DEFAULT_REST_TIMER_SECONDS,
            preferences.getRestTimerSeconds(),
        )

        preferences.setRestTimerSeconds(120)

        assertEquals(120, preferences.getRestTimerSeconds())
    }

    @Test
    fun catalog_seeded_flag_prevents_duplicate_seed() = runBlocking {
        assertFalse(preferences.isCatalogSeeded())

        catalogSeeder.seedIfEmpty()
        val countAfterFirstSeed = database.exerciseDao().count()

        assertTrue(countAfterFirstSeed > 0)
        assertTrue(preferences.isCatalogSeeded())

        catalogSeeder.seedIfEmpty()

        assertEquals(countAfterFirstSeed, database.exerciseDao().count())
    }

    @Test
    fun transaction_rolls_back_when_block_fails() = runBlocking {
        val exerciseId = ExerciseId.generate()
        val instant = Instant.parse("2026-06-19T10:00:00Z")
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
        val (sessionEntity, exercises) = WorkoutSessionMapper.toEntity(session)

        try {
            transactionRunner.run {
                database.workoutSessionDao().saveSession(sessionEntity, exercises)
                val setLog = SetLog.create(
                    sessionId = session.id,
                    exerciseId = exerciseId,
                    setNumber = 1,
                    weight = Weight.fromKilograms(50.0),
                    reps = RepCount(10),
                    completedAt = instant,
                )
                database.setLogDao().upsert(SetLogMapper.toEntity(setLog))
                throw RuntimeException("forced failure")
            }
        } catch (_: RuntimeException) {
            // expected
        }

        assertEquals(0, database.setLogDao().findBySession(session.id.toString()).size)
        assertEquals(null, database.workoutSessionDao().findById(session.id.toString()))
    }
}
