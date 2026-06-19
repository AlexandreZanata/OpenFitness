package com.openfitness.domain.state

import com.openfitness.domain.exception.InvalidStateTransitionException
import com.openfitness.domain.valueobject.SessionStatus

object WorkoutSessionStateMachine {
    fun transition(from: SessionStatus, to: SessionStatus) {
        if (!isValid(from, to)) {
            throw InvalidStateTransitionException(from.name, to.name)
        }
    }

    fun isValid(from: SessionStatus, to: SessionStatus): Boolean = when (from) {
        SessionStatus.PLANNED -> to == SessionStatus.IN_PROGRESS || to == SessionStatus.CANCELLED
        SessionStatus.IN_PROGRESS -> to == SessionStatus.COMPLETED || to == SessionStatus.CANCELLED
        SessionStatus.COMPLETED, SessionStatus.CANCELLED -> false
    }

    fun isTerminal(status: SessionStatus): Boolean =
        status == SessionStatus.COMPLETED || status == SessionStatus.CANCELLED
}
