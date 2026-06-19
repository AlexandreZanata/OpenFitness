package com.openfitness.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.openfitness.data.local.dao.ExerciseDao
import com.openfitness.data.local.dao.PersonalRecordDao
import com.openfitness.data.local.dao.RecordCorrectionDao
import com.openfitness.data.local.dao.SetLogDao
import com.openfitness.data.local.dao.WorkoutSessionDao
import com.openfitness.data.local.dao.WorkoutTemplateDao
import com.openfitness.data.local.entity.ExerciseEntity
import com.openfitness.data.local.entity.PersonalRecordEntity
import com.openfitness.data.local.entity.PersonalRecordHistoryEntity
import com.openfitness.data.local.entity.RecordCorrectionEntity
import com.openfitness.data.local.entity.SessionExerciseEntity
import com.openfitness.data.local.entity.SetLogEntity
import com.openfitness.data.local.entity.TemplateExerciseEntity
import com.openfitness.data.local.entity.WorkoutSessionEntity
import com.openfitness.data.local.entity.WorkoutTemplateEntity

@Database(
    entities = [
        ExerciseEntity::class,
        WorkoutTemplateEntity::class,
        TemplateExerciseEntity::class,
        WorkoutSessionEntity::class,
        SessionExerciseEntity::class,
        SetLogEntity::class,
        PersonalRecordEntity::class,
        PersonalRecordHistoryEntity::class,
        RecordCorrectionEntity::class,
    ],
    version = 1,
    exportSchema = true,
)
abstract class OpenFitnessDatabase : RoomDatabase() {
    abstract fun exerciseDao(): ExerciseDao
    abstract fun workoutTemplateDao(): WorkoutTemplateDao
    abstract fun workoutSessionDao(): WorkoutSessionDao
    abstract fun setLogDao(): SetLogDao
    abstract fun personalRecordDao(): PersonalRecordDao
    abstract fun recordCorrectionDao(): RecordCorrectionDao
}
