package com.openfitness.domain.valueobject

data class Duration(val seconds: Long) {
    init {
        require(seconds >= 0) { "Duration cannot be negative" }
    }

    companion object {
        fun fromSeconds(seconds: Long): Duration = Duration(seconds)

        fun fromMinutes(minutes: Int): Duration = Duration(minutes * 60L)
    }
}
