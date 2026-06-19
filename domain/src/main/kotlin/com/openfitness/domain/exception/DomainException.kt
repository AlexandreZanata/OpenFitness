package com.openfitness.domain.exception

open class DomainException(message: String) : RuntimeException(message)

class InvalidStateTransitionException(
    val from: String,
    val to: String,
) : DomainException("Invalid state transition from $from to $to")

class DuplicateExerciseNameException(
    val name: String,
) : DomainException("Exercise name already exists: $name")

class ImmutableRecordException(
    message: String,
) : DomainException(message)

class RecordNotFoundException(
    val recordId: String,
) : DomainException("Record not found: $recordId")
