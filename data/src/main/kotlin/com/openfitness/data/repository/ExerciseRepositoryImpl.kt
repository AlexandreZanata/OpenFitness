package com.openfitness.data.repository

import android.content.Context
import com.openfitness.data.local.dao.ExerciseDao
import com.openfitness.data.mapper.ExerciseMapper
import com.openfitness.data.parser.BundledExerciseCatalogParser
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.repository.CatalogSeeder
import com.openfitness.domain.repository.ExerciseRepository
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext

@Singleton
class ExerciseRepositoryImpl @Inject constructor(
    private val exerciseDao: ExerciseDao,
) : ExerciseRepository {

    override suspend fun findById(id: ExerciseId): Exercise? =
        exerciseDao.findById(id.toString())?.let(ExerciseMapper::toDomain)

    override suspend fun search(query: String, muscleGroup: MuscleGroup?): List<Exercise> =
        exerciseDao.search(query.trim(), muscleGroup?.name).map(ExerciseMapper::toDomain)

    override suspend fun findAllNames(): List<String> = exerciseDao.findAllNames()

    override suspend fun save(exercise: Exercise) {
        exerciseDao.upsert(ExerciseMapper.toEntity(exercise))
    }

    override fun observeAll(): Flow<List<Exercise>> =
        exerciseDao.observeAll().map { entities -> entities.map(ExerciseMapper::toDomain) }
}

@Singleton
class CatalogSeederImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val exerciseDao: ExerciseDao,
    private val parser: BundledExerciseCatalogParser,
) : CatalogSeeder {

    override suspend fun isSeeded(): Boolean = withContext(Dispatchers.IO) {
        exerciseDao.count() > 0
    }

    override suspend fun seedIfEmpty() = withContext(Dispatchers.IO) {
        if (isSeeded()) return@withContext
        val json = context.assets.open("exercises/catalog.json")
            .bufferedReader()
            .use { it.readText() }
        val exercises = parser.parse(json)
        exerciseDao.upsertAll(exercises.map(ExerciseMapper::toEntity))
    }
}
