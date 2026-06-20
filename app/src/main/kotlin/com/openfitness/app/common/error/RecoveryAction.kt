package com.openfitness.app.common.error

import com.openfitness.application.error.AppError

sealed class RecoveryAction {
    data object Retry : RecoveryAction()
    data object Dismiss : RecoveryAction()
    data object NavigateBack : RecoveryAction()
}

fun AppError.toRecoveryAction(): RecoveryAction? = when (this) {
    AppError.StorageError -> RecoveryAction.Retry
    AppError.NotFound -> RecoveryAction.NavigateBack
    AppError.ValidationError -> RecoveryAction.Dismiss
    AppError.ConflictError -> RecoveryAction.Dismiss
    is AppError.DuplicateExerciseName -> RecoveryAction.Dismiss
    is AppError.InvalidStateTransition -> RecoveryAction.Dismiss
}
