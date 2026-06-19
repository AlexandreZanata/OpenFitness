package com.openfitness.application.error

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.DuplicateExerciseNameException
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.exception.InvalidStateTransitionException
import com.openfitness.domain.exception.RecordNotFoundException
import java.io.IOException

object DomainExceptionMapper {
    fun map(throwable: Throwable): AppError = when (throwable) {
        is DuplicateExerciseNameException -> AppError.DuplicateExerciseName(throwable.name)
        is InvalidStateTransitionException -> AppError.InvalidStateTransition(throwable.from, throwable.to)
        is RecordNotFoundException -> AppError.NotFound
        is ImmutableRecordException -> AppError.ValidationError
        is DomainException -> AppError.ValidationError
        is IOException -> AppError.StorageError
        else -> AppError.StorageError
    }
}

suspend fun <T> runUseCase(block: suspend () -> T): UseCaseResult<T> =
    try {
        UseCaseResult.success(block())
    } catch (throwable: Throwable) {
        UseCaseResult.failure(DomainExceptionMapper.map(throwable))
    }
