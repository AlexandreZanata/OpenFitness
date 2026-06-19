package com.openfitness.application.error

sealed class AppError {
    data object ValidationError : AppError()

    data object NotFound : AppError()

    data object StorageError : AppError()

    data object ConflictError : AppError()

    data class DuplicateExerciseName(val name: String) : AppError()

    data class InvalidStateTransition(val from: String, val to: String) : AppError()
}
