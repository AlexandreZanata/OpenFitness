package com.openfitness.domain.valueobject

import java.util.UUID

@JvmInline
value class TemplateId(val value: UUID) {
    companion object {
        fun generate(): TemplateId = TemplateId(UUID.randomUUID())

        fun fromString(raw: String): TemplateId = TemplateId(UUID.fromString(raw.trim()))
    }
}
