package com.openfitness.domain.exception

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class DomainExceptionCoverageTest {

    @Test
    fun `all exception types retain message`() {
        assertEquals("x", DomainException("x").message)
        assertEquals("Invalid state transition from A to B", InvalidStateTransitionException("A", "B").message)
        assertEquals("Exercise name already exists: Curl", DuplicateExerciseNameException("Curl").message)
        assertEquals("locked", ImmutableRecordException("locked").message)
        assertEquals("Record not found: id-1", RecordNotFoundException("id-1").message)
    }
}
