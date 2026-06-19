package com.openfitness.domain.valueobject

import java.util.UUID

@JvmInline
value class SessionId(val value: UUID) {
    init {
        require(value.version() == 4) { "SessionId must be UUID v4" }
    }

    override fun toString(): String = value.toString()

    companion object {
        fun generate(): SessionId = SessionId(UUID.randomUUID())

        fun fromString(raw: String): SessionId = SessionId(UUID.fromString(raw.trim()))
    }
}
