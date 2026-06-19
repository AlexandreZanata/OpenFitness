package com.openfitness.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "exercises")
data class ExerciseEntity(
    @PrimaryKey val id: String,
    val name: String,
    @ColumnInfo(name = "primary_muscle_group") val primaryMuscleGroup: String,
    @ColumnInfo(name = "equipment_type") val equipmentType: String,
    @ColumnInfo(name = "is_custom") val isCustom: Boolean,
    @ColumnInfo(name = "created_at") val createdAt: Long,
)

@Entity(tableName = "workout_templates")
data class WorkoutTemplateEntity(
    @PrimaryKey val id: String,
    val name: String,
    @ColumnInfo(name = "created_at") val createdAt: Long,
    @ColumnInfo(name = "updated_at") val updatedAt: Long,
)

@Entity(
    tableName = "template_exercises",
    primaryKeys = ["template_id", "exercise_id"],
)
data class TemplateExerciseEntity(
    @ColumnInfo(name = "template_id") val templateId: String,
    @ColumnInfo(name = "exercise_id") val exerciseId: String,
    @ColumnInfo(name = "order_index") val orderIndex: Int,
    @ColumnInfo(name = "target_sets") val targetSets: Int,
    @ColumnInfo(name = "target_reps") val targetReps: Int?,
    @ColumnInfo(name = "target_weight_kg") val targetWeightKg: Double?,
)

@Entity(tableName = "workout_sessions")
data class WorkoutSessionEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "template_id") val templateId: String?,
    val status: String,
    @ColumnInfo(name = "started_at") val startedAt: Long?,
    @ColumnInfo(name = "completed_at") val completedAt: Long?,
    @ColumnInfo(name = "cancelled_at") val cancelledAt: Long?,
)

@Entity(
    tableName = "session_exercises",
    primaryKeys = ["session_id", "exercise_id"],
)
data class SessionExerciseEntity(
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "exercise_id") val exerciseId: String,
    @ColumnInfo(name = "order_index") val orderIndex: Int,
)

@Entity(tableName = "set_logs")
data class SetLogEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "exercise_id") val exerciseId: String,
    @ColumnInfo(name = "set_number") val setNumber: Int,
    @ColumnInfo(name = "weight_kg") val weightKg: Double?,
    val reps: Int?,
    @ColumnInfo(name = "completed_at") val completedAt: Long,
)

@Entity(
    tableName = "personal_records",
    primaryKeys = ["exercise_id", "metric"],
)
data class PersonalRecordEntity(
    @ColumnInfo(name = "exercise_id") val exerciseId: String,
    val metric: String,
    val value: Double,
    @ColumnInfo(name = "achieved_at") val achievedAt: Long,
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "set_log_id") val setLogId: String,
)

@Entity(tableName = "personal_record_history")
data class PersonalRecordHistoryEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "exercise_id") val exerciseId: String,
    val metric: String,
    val value: Double,
    @ColumnInfo(name = "achieved_at") val achievedAt: Long,
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "set_log_id") val setLogId: String,
    @ColumnInfo(name = "superseded_at") val supersededAt: Long,
)

@Entity(tableName = "record_corrections")
data class RecordCorrectionEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "session_id") val sessionId: String,
    @ColumnInfo(name = "original_set_log_id") val originalSetLogId: String,
    @ColumnInfo(name = "corrected_weight_kg") val correctedWeightKg: Double?,
    @ColumnInfo(name = "corrected_reps") val correctedReps: Int?,
    val reason: String?,
    @ColumnInfo(name = "created_at") val createdAt: Long,
)
