package com.openfitness.domain.model

import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.Weight
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Test
import java.time.Instant

class RecordCorrectionTest {

    @Test
    fun `GIVEN completed set WHEN create correction THEN append-only record`() {
        val correction = RecordCorrection.create(
            sessionId = SessionId.generate(),
            originalSetLogId = SetLogId.generate(),
            correctedWeight = Weight.fromKilograms(62.5),
            correctedReps = RepCount(10),
            reason = "Transcription error",
        )
        assertNotNull(correction.id)
    }
}
