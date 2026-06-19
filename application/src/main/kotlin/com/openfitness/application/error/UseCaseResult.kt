package com.openfitness.application.error

typealias Result<T, E> = UseCaseResult<T>

sealed class UseCaseResult<out T> {
    data class Success<T>(val value: T) : UseCaseResult<T>()

    data class Failure(val error: AppError) : UseCaseResult<Nothing>()

    companion object {
        fun <T> success(value: T): UseCaseResult<T> = Success(value)

        fun failure(error: AppError): UseCaseResult<Nothing> = Failure(error)
    }
}

inline fun <T> UseCaseResult<T>.getOrNull(): T? = when (this) {
    is UseCaseResult.Success -> value
    is UseCaseResult.Failure -> null
}

inline fun <T> UseCaseResult<T>.errorOrNull(): AppError? = when (this) {
    is UseCaseResult.Success -> null
    is UseCaseResult.Failure -> error
}
