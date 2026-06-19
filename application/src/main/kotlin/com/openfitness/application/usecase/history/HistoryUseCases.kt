package com.openfitness.application.usecase.history

import com.openfitness.domain.model.PersonalRecord
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.repository.PersonalRecordRepository
import com.openfitness.domain.repository.WorkoutSessionRepository
import kotlinx.coroutines.flow.Flow

private const val HISTORY_LIMIT = 100

class ViewWorkoutHistoryUseCase(
    private val repo: WorkoutSessionRepository,
) {
    operator fun invoke(): Flow<List<WorkoutSession>> = repo.observeCompleted(HISTORY_LIMIT)
}

class ViewPersonalRecordsUseCase(
    private val repo: PersonalRecordRepository,
) {
    operator fun invoke(): Flow<List<PersonalRecord>> = repo.observeAll()
}
