package com.openfitness.application.usecase.session

import com.openfitness.domain.repository.RecordCorrectionRepository
import com.openfitness.domain.valueobject.SessionId

class GetRecordCorrectionsUseCase(
    private val correctionRepo: RecordCorrectionRepository,
) {
    suspend operator fun invoke(sessionId: SessionId) = correctionRepo.findBySession(sessionId)
}
