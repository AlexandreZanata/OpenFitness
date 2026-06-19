package com.openfitness.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.openfitness.data.local.entity.TemplateExerciseEntity
import com.openfitness.data.local.entity.WorkoutTemplateEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface WorkoutTemplateDao {
    @Query("SELECT * FROM workout_templates WHERE id = :id LIMIT 1")
    suspend fun findById(id: String): WorkoutTemplateEntity?

    @Query("SELECT * FROM template_exercises WHERE template_id = :templateId ORDER BY order_index ASC")
    suspend fun findExercises(templateId: String): List<TemplateExerciseEntity>

    @Query("SELECT * FROM workout_templates ORDER BY name ASC")
    fun observeAll(): Flow<List<WorkoutTemplateEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertTemplate(template: WorkoutTemplateEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertExercises(exercises: List<TemplateExerciseEntity>)

    @Query("DELETE FROM template_exercises WHERE template_id = :templateId")
    suspend fun deleteExercises(templateId: String)

    @Query("DELETE FROM workout_templates WHERE id = :id")
    suspend fun deleteTemplate(id: String)

    @Transaction
    suspend fun saveTemplate(
        template: WorkoutTemplateEntity,
        exercises: List<TemplateExerciseEntity>,
    ) {
        upsertTemplate(template)
        deleteExercises(template.id)
        if (exercises.isNotEmpty()) {
            upsertExercises(exercises)
        }
    }
}
