package com.openfitness.app.di

import com.openfitness.application.usecase.bootstrap.SeedCatalogUseCase
import com.openfitness.application.usecase.exerciselibrary.BrowseExercisesUseCase
import com.openfitness.application.usecase.exerciselibrary.CreateCustomExerciseUseCase
import com.openfitness.application.usecase.exerciselibrary.GetExerciseUseCase
import com.openfitness.application.usecase.exerciselibrary.UpdateCustomExerciseUseCase
import com.openfitness.application.usecase.history.ViewPersonalRecordsUseCase
import com.openfitness.application.usecase.history.ViewWorkoutHistoryUseCase
import com.openfitness.application.usecase.preferences.ObserveRestTimerUseCase
import com.openfitness.application.usecase.session.CompleteWorkoutSessionUseCase
import com.openfitness.application.usecase.session.CorrectCompletedSetUseCase
import com.openfitness.application.usecase.session.EditSetUseCase
import com.openfitness.application.usecase.session.GetRecordCorrectionsUseCase
import com.openfitness.application.usecase.session.GetWorkoutSessionUseCase
import com.openfitness.application.usecase.session.LogSetUseCase
import com.openfitness.application.usecase.session.StartWorkoutSessionUseCase
import com.openfitness.application.usecase.template.CreateWorkoutTemplateUseCase
import com.openfitness.application.usecase.template.ListWorkoutTemplatesUseCase
import com.openfitness.application.usecase.template.UpdateWorkoutTemplateUseCase
import com.openfitness.domain.repository.CatalogSeeder
import com.openfitness.domain.repository.ExerciseRepository
import com.openfitness.domain.repository.PersonalRecordRepository
import com.openfitness.domain.repository.RecordCorrectionRepository
import com.openfitness.domain.repository.SetLogRepository
import com.openfitness.domain.repository.TransactionRunner
import com.openfitness.domain.repository.UserPreferencesRepository
import com.openfitness.domain.repository.WorkoutSessionRepository
import com.openfitness.domain.repository.WorkoutTemplateRepository
import com.openfitness.domain.rule.ExerciseNameUniquenessRule
import com.openfitness.domain.rule.PersonalRecordEvaluationRule
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object UseCaseModule {

    @Provides @Singleton
    fun provideExerciseNameUniquenessRule(): ExerciseNameUniquenessRule = ExerciseNameUniquenessRule()

    @Provides @Singleton
    fun providePersonalRecordEvaluationRule(): PersonalRecordEvaluationRule = PersonalRecordEvaluationRule()

    @Provides @Singleton
    fun provideSeedCatalogUseCase(catalogSeeder: CatalogSeeder): SeedCatalogUseCase =
        SeedCatalogUseCase(catalogSeeder)

    @Provides @Singleton
    fun provideBrowseExercisesUseCase(repo: ExerciseRepository): BrowseExercisesUseCase =
        BrowseExercisesUseCase(repo)

    @Provides @Singleton
    fun provideGetExerciseUseCase(repo: ExerciseRepository): GetExerciseUseCase =
        GetExerciseUseCase(repo)

    @Provides @Singleton
    fun provideCreateCustomExerciseUseCase(
        repo: ExerciseRepository,
        rule: ExerciseNameUniquenessRule,
    ): CreateCustomExerciseUseCase = CreateCustomExerciseUseCase(repo, rule)

    @Provides @Singleton
    fun provideUpdateCustomExerciseUseCase(
        repo: ExerciseRepository,
        rule: ExerciseNameUniquenessRule,
    ): UpdateCustomExerciseUseCase = UpdateCustomExerciseUseCase(repo, rule)

    @Provides @Singleton
    fun provideListWorkoutTemplatesUseCase(repo: WorkoutTemplateRepository): ListWorkoutTemplatesUseCase =
        ListWorkoutTemplatesUseCase(repo)

    @Provides @Singleton
    fun provideCreateWorkoutTemplateUseCase(repo: WorkoutTemplateRepository): CreateWorkoutTemplateUseCase =
        CreateWorkoutTemplateUseCase(repo)

    @Provides @Singleton
    fun provideUpdateWorkoutTemplateUseCase(repo: WorkoutTemplateRepository): UpdateWorkoutTemplateUseCase =
        UpdateWorkoutTemplateUseCase(repo)

    @Provides @Singleton
    fun provideStartWorkoutSessionUseCase(repo: WorkoutSessionRepository): StartWorkoutSessionUseCase =
        StartWorkoutSessionUseCase(repo)

    @Provides @Singleton
    fun provideGetWorkoutSessionUseCase(repo: WorkoutSessionRepository): GetWorkoutSessionUseCase =
        GetWorkoutSessionUseCase(repo)

    @Provides @Singleton
    fun provideGetRecordCorrectionsUseCase(repo: RecordCorrectionRepository): GetRecordCorrectionsUseCase =
        GetRecordCorrectionsUseCase(repo)

    @Provides @Singleton
    fun provideLogSetUseCase(
        sessionRepo: WorkoutSessionRepository,
        setLogRepo: SetLogRepository,
        transactionRunner: TransactionRunner,
    ): LogSetUseCase = LogSetUseCase(sessionRepo, setLogRepo, transactionRunner)

    @Provides @Singleton
    fun provideEditSetUseCase(
        sessionRepo: WorkoutSessionRepository,
        transactionRunner: TransactionRunner,
    ): EditSetUseCase = EditSetUseCase(sessionRepo, transactionRunner)

    @Provides @Singleton
    fun provideCompleteWorkoutSessionUseCase(
        sessionRepo: WorkoutSessionRepository,
        prRepo: PersonalRecordRepository,
        prRule: PersonalRecordEvaluationRule,
        transactionRunner: TransactionRunner,
    ): CompleteWorkoutSessionUseCase =
        CompleteWorkoutSessionUseCase(sessionRepo, prRepo, prRule, transactionRunner)

    @Provides @Singleton
    fun provideCorrectCompletedSetUseCase(
        sessionRepo: WorkoutSessionRepository,
        correctionRepo: RecordCorrectionRepository,
        transactionRunner: TransactionRunner,
    ): CorrectCompletedSetUseCase =
        CorrectCompletedSetUseCase(sessionRepo, correctionRepo, transactionRunner)

    @Provides @Singleton
    fun provideViewWorkoutHistoryUseCase(repo: WorkoutSessionRepository): ViewWorkoutHistoryUseCase =
        ViewWorkoutHistoryUseCase(repo)

    @Provides @Singleton
    fun provideViewPersonalRecordsUseCase(repo: PersonalRecordRepository): ViewPersonalRecordsUseCase =
        ViewPersonalRecordsUseCase(repo)

    @Provides @Singleton
    fun provideObserveRestTimerUseCase(repo: UserPreferencesRepository): ObserveRestTimerUseCase =
        ObserveRestTimerUseCase(repo)
}
