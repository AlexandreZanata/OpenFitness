package com.openfitness.domain.valueobject

@JvmInline
value class RepCount(val value: Int) {
    init {
        require(value >= 1) { "Rep count must be at least 1" }
    }
}
