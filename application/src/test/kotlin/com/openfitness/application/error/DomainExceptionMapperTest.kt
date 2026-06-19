package com.openfitness.application.error

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.DuplicateExerciseNameException
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.exception.InvalidStateTransitionException
import com.openfitness.domain.exception.RecordNotFoundException
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Test

class DomainExceptionMapperTest {

    @Test
    fun `GIVEN duplicate name WHEN map THEN DuplicateExerciseName`() {
        val error = DomainExceptionMapper.map(DuplicateExerciseNameException("Squat"))
        assertInstanceOf(AppError.DuplicateExerciseName::class.java, error)
        assertEquals("Squat", (error as AppError.DuplicateExerciseName).name)
    }

    @Test
    fun `GIVEN invalid transition WHEN map THEN InvalidStateTransition`() {
        val error = DomainExceptionMapper.map(InvalidStateTransitionException("PLANNED", "COMPLETED"))
        assertInstanceOf(AppError.InvalidStateTransition::class.java, error)
    }

    @Test
    fun `GIVEN immutable record WHEN map THEN ValidationError`() {
        val error = DomainExceptionMapper.map(ImmutableRecordException("blocked"))
        assertEquals(AppError.ValidationError, error)
    }

    @Test
    fun `GIVEN record not found WHEN map THEN NotFound`() {
        val error = DomainExceptionMapper.map(RecordNotFoundException("id"))
        assertEquals(AppError.NotFound, error)
    }

    @Test
    fun `GIVEN domain validation WHEN map THEN ValidationError`() {
        val error = DomainExceptionMapper.map(DomainException("invalid"))
        assertEquals(AppError.ValidationError, error)
    }
}
