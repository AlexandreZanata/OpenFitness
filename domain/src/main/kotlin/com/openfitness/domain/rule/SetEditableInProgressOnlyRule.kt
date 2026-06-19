package com.openfitness.domain.rule

import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.valueobject.SessionStatus

class SetEditableInProgressOnlyRule {
    fun validate(status: SessionStatus) {
        if (status != SessionStatus.IN_PROGRESS) {
            throw ImmutableRecordException("Set logs are editable only while session is in progress")
        }
    }
}
