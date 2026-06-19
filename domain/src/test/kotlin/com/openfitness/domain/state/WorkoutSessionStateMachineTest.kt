package com.openfitness.domain.state

import com.openfitness.domain.exception.InvalidStateTransitionException
import com.openfitness.domain.valueobject.SessionStatus
import org.junit.jupiter.api.Assertions.assertDoesNotThrow
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test

class WorkoutSessionStateMachineTest {

    @Test
    fun `GIVEN PLANNED WHEN start to IN_PROGRESS THEN valid`() {
        assertDoesNotThrow {
            WorkoutSessionStateMachine.transition(SessionStatus.PLANNED, SessionStatus.IN_PROGRESS)
        }
    }

    @Test
    fun `GIVEN COMPLETED WHEN any transition THEN InvalidStateTransitionException`() {
        assertThrows(InvalidStateTransitionException::class.java) {
            WorkoutSessionStateMachine.transition(SessionStatus.COMPLETED, SessionStatus.IN_PROGRESS)
        }
    }

    @Test
    fun `GIVEN PLANNED WHEN complete THEN invalid`() {
        assertThrows(InvalidStateTransitionException::class.java) {
            WorkoutSessionStateMachine.transition(SessionStatus.PLANNED, SessionStatus.COMPLETED)
        }
    }
}
