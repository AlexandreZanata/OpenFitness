package com.openfitness.domain.valueobject

import java.util.UUID

@JvmInline
value class SetLogId(val value: UUID) {
    companion object {
        fun generate(): SetLogId = SetLogId(UUID.randomUUID())

        fun fromString(raw: String): SetLogId = SetLogId(UUID.fromString(raw.trim()))
    }
}
