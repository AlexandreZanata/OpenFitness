package com.openfitness.data.repository

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.openfitness.data.local.OpenFitnessDatabase
import com.openfitness.data.parser.BundledExerciseCatalogParser
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.model.SessionExercise
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.Weight
import java.time.Instant
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class RepositoryIntegrationTest {

    private lateinit var database: OpenFitnessDatabase
    private lateinit var exerciseRepository: ExerciseRepositoryImpl
    private lateinit var catalogSeeder: CatalogSeederImpl
    private lateinit var sessionRepository: WorkoutSessionRepositoryImpl
    private lateinit var setLogRepository: SetLogRepositoryImpl
    private lateinit var recordCorrectionRepository: RecordCorrectionRepositoryImpl

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, OpenFitnessDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        exerciseRepository = ExerciseRepositoryImpl(database.exerciseDao())
        catalogSeeder = CatalogSeederImpl(context, database.exerciseDao(), BundledExerciseCatalogParser())
        sessionRepository = WorkoutSessionRepositoryImpl(
            database,
            database.workoutSessionDao(),
            database.setLogDao(),
        )
        setLogRepository = SetLogRepositoryImpl(database.setLogDao(), database.workoutSessionDao())
        recordCorrectionRepository = RecordCorrectionRepositoryImpl(database.recordCorrectionDao())
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun seed_and_search_bundled_exercises() = runBlocking {
        catalogSeeder.seedIfEmpty()
        assertTrue(catalogSeeder.isSeeded())
        val results = exerciseRepository.search("press", null)
        assertTrue(results.isNotEmpty())
        assertTrue(results.all { !it.isCustom })
    }

    @Test
    fun save_and_load_custom_exercise() = runBlocking {
        val exercise = Exercise.createCustom("Incline Curl", MuscleGroup.BICEPS, EquipmentType.DUMBBELL) {}
        exerciseRepository.save(exercise)
        val loaded = exerciseRepository.findById(exercise.id)
        assertEquals(exercise.name, loaded?.name)
        assertEquals(EquipmentType.DUMBBELL, loaded?.equipmentType)
    }

    @Test
    fun completed_session_set_logs_cannot_be_modified() = runBlocking {
        val exerciseId = ExerciseId.generate()
        val instant = Instant.now()
        var session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
            .complete(instant)
        sessionRepository.save(session)

        val setLog = SetLog.create(
            sessionId = session.id,
            exerciseId = exerciseId,
            setNumber = 1,
            weight = Weight.fromKilograms(60.0),
            reps = RepCount(5),
            completedAt = instant,
        )

        assertThrows(ImmutableRecordException::class.java) {
            runBlocking { setLogRepository.save(setLog) }
        }
    }

    @Test
    fun record_correction_is_append_only() = runBlocking {
        val exerciseId = ExerciseId.generate()
        val instant = Instant.now()
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
            .complete(instant)
        sessionRepository.save(session)

        val originalSet = SetLog.create(
            sessionId = session.id,
            exerciseId = exerciseId,
            setNumber = 1,
            weight = Weight.fromKilograms(80.0),
            reps = RepCount(5),
            completedAt = instant,
        )
        database.setLogDao().upsert(
            com.openfitness.data.mapper.SetLogMapper.toEntity(originalSet),
        )

        val correction = com.openfitness.domain.model.RecordCorrection.create(
            sessionId = session.id,
            originalSetLogId = originalSet.id,
            correctedWeight = Weight.fromKilograms(85.0),
            correctedReps = RepCount(5),
            reason = "Wrong plate loaded",
        )
        recordCorrectionRepository.save(correction)

        val loaded = recordCorrectionRepository.findBySession(session.id)
        assertEquals(1, loaded.size)
        assertEquals(originalSet.id, loaded.first().originalSetLogId)
        assertEquals(85.0, loaded.first().correctedWeight?.kilograms)
    }
}
