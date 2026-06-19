package com.openfitness.application.usecase.session

import com.openfitness.domain.repository.WorkoutSessionRepository
import com.openfitness.domain.valueobject.SessionId

class GetWorkoutSessionUseCase(
    private val sessionRepo: WorkoutSessionRepository,
) {
    suspend operator fun invoke(sessionId: SessionId) = sessionRepo.findById(sessionId)
}
