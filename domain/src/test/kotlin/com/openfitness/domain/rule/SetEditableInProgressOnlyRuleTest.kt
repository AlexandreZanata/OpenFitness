package com.openfitness.domain.rule

import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.valueobject.SessionStatus
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class SetEditableInProgressOnlyRuleTest {

    @Test
    fun `GIVEN COMPLETED session WHEN validate edit THEN ImmutableRecordException`() {
        assertThrows(ImmutableRecordException::class.java) {
            SetEditableInProgressOnlyRule().validate(SessionStatus.COMPLETED)
        }
    }
}
