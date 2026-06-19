package com.openfitness.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.openfitness.data.local.entity.ExerciseEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ExerciseDao {
    @Query("SELECT * FROM exercises WHERE id = :id LIMIT 1")
    suspend fun findById(id: String): ExerciseEntity?

    @Query("SELECT * FROM exercises ORDER BY name ASC")
    fun observeAll(): Flow<List<ExerciseEntity>>

    @Query(
        """
        SELECT * FROM exercises
        WHERE (:query = '' OR name LIKE '%' || :query || '%' COLLATE NOCASE)
        AND (:muscleGroup IS NULL OR primary_muscle_group = :muscleGroup)
        ORDER BY name ASC
        """,
    )
    suspend fun search(query: String, muscleGroup: String?): List<ExerciseEntity>

    @Query("SELECT name FROM exercises")
    suspend fun findAllNames(): List<String>

    @Query("SELECT COUNT(*) FROM exercises")
    suspend fun count(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(exercises: List<ExerciseEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(exercise: ExerciseEntity)
}
