package com.openfitness.app.navigation

object Routes {
    const val EXERCISE_LIBRARY = "exercise_library"
    const val TEMPLATES = "templates"
    const val HISTORY = "history"
    const val PERSONAL_RECORDS = "personal_records"
    const val ACTIVE_SESSION = "active_session/{sessionId}"
    const val SESSION_SUMMARY = "session_summary/{sessionId}"

    fun activeSession(sessionId: String): String = "active_session/$sessionId"
    fun sessionSummary(sessionId: String): String = "session_summary/$sessionId"
}
