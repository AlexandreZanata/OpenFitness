package com.openfitness.data.di

import android.content.Context
import androidx.room.Room
import com.openfitness.data.local.OpenFitnessDatabase
import com.openfitness.data.local.dao.ExerciseDao
import com.openfitness.data.local.dao.PersonalRecordDao
import com.openfitness.data.local.dao.RecordCorrectionDao
import com.openfitness.data.local.dao.SetLogDao
import com.openfitness.data.local.dao.WorkoutSessionDao
import com.openfitness.data.local.dao.WorkoutTemplateDao
import com.openfitness.data.parser.BundledExerciseCatalogParser
import com.openfitness.data.preferences.UserPreferencesDataStore
import com.openfitness.data.repository.CatalogSeederImpl
import com.openfitness.data.transaction.RoomTransactionRunner
import com.openfitness.data.repository.ExerciseRepositoryImpl
import com.openfitness.data.repository.PersonalRecordRepositoryImpl
import com.openfitness.data.repository.RecordCorrectionRepositoryImpl
import com.openfitness.data.repository.SetLogRepositoryImpl
import com.openfitness.data.repository.WorkoutSessionRepositoryImpl
import com.openfitness.data.repository.WorkoutTemplateRepositoryImpl
import com.openfitness.domain.repository.CatalogSeeder
import com.openfitness.domain.repository.ExerciseRepository
import com.openfitness.domain.repository.PersonalRecordRepository
import com.openfitness.domain.repository.RecordCorrectionRepository
import com.openfitness.domain.repository.SetLogRepository
import com.openfitness.domain.repository.WorkoutSessionRepository
import com.openfitness.domain.repository.TransactionRunner
import com.openfitness.domain.repository.WorkoutTemplateRepository
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): OpenFitnessDatabase =
        Room.databaseBuilder(
            context,
            OpenFitnessDatabase::class.java,
            "open_fitness.db",
        ).build()

    @Provides fun provideExerciseDao(db: OpenFitnessDatabase): ExerciseDao = db.exerciseDao()
    @Provides fun provideTemplateDao(db: OpenFitnessDatabase): WorkoutTemplateDao = db.workoutTemplateDao()
    @Provides fun provideSessionDao(db: OpenFitnessDatabase): WorkoutSessionDao = db.workoutSessionDao()
    @Provides fun provideSetLogDao(db: OpenFitnessDatabase): SetLogDao = db.setLogDao()
    @Provides fun providePersonalRecordDao(db: OpenFitnessDatabase): PersonalRecordDao = db.personalRecordDao()
    @Provides fun provideRecordCorrectionDao(db: OpenFitnessDatabase): RecordCorrectionDao = db.recordCorrectionDao()

    @Provides
    @Singleton
    fun provideCatalogParser(): BundledExerciseCatalogParser = BundledExerciseCatalogParser()
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds @Singleton
    abstract fun bindExerciseRepository(impl: ExerciseRepositoryImpl): ExerciseRepository

    @Binds @Singleton
    abstract fun bindCatalogSeeder(impl: CatalogSeederImpl): CatalogSeeder

    @Binds @Singleton
    abstract fun bindWorkoutTemplateRepository(impl: WorkoutTemplateRepositoryImpl): WorkoutTemplateRepository

    @Binds @Singleton
    abstract fun bindWorkoutSessionRepository(impl: WorkoutSessionRepositoryImpl): WorkoutSessionRepository

    @Binds @Singleton
    abstract fun bindSetLogRepository(impl: SetLogRepositoryImpl): SetLogRepository

    @Binds @Singleton
    abstract fun bindPersonalRecordRepository(impl: PersonalRecordRepositoryImpl): PersonalRecordRepository

    @Binds @Singleton
    abstract fun bindRecordCorrectionRepository(impl: RecordCorrectionRepositoryImpl): RecordCorrectionRepository

    @Binds @Singleton
    abstract fun bindTransactionRunner(impl: RoomTransactionRunner): TransactionRunner
}
