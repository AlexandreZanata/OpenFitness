package com.openfitness.app.common.error

import android.content.res.Resources
import com.openfitness.app.R
import com.openfitness.application.error.AppError

fun AppError.toMessage(resources: Resources): String = when (this) {
    AppError.ValidationError -> resources.getString(R.string.error_validation)
    AppError.NotFound -> resources.getString(R.string.error_not_found)
    AppError.StorageError -> resources.getString(R.string.error_storage)
    AppError.ConflictError -> resources.getString(R.string.error_session_in_progress)
    is AppError.DuplicateExerciseName -> resources.getString(R.string.error_duplicate_exercise_name, name)
    is AppError.InvalidStateTransition -> resources.getString(R.string.error_invalid_state, from, to)
}
