package com.openfitness.domain.model

import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.rule.ExerciseNameUniquenessRule
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.MuscleGroup
import com.openfitness.domain.valueobject.TemplateId
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test
import java.time.Instant

class AdditionalCoverageTest {

    private val instant = Instant.parse("2026-06-19T15:00:00Z")
    private val exerciseId = com.openfitness.domain.valueobject.ExerciseId.generate()

    @Test
    fun `GIVEN completed session WHEN cancel THEN ImmutableRecordException`() {
        val session = WorkoutSession.create(null, listOf(SessionExercise(exerciseId, 0)))
            .start(instant)
            .complete(instant)
        assertThrows(ImmutableRecordException::class.java) {
            session.cancel(instant)
        }
    }

    @Test
    fun `GIVEN empty exercises WHEN create session THEN BR-003`() {
        assertThrows(DomainException::class.java) {
            WorkoutSession.create(null, emptyList())
        }
    }

    @Test
    fun `GIVEN template restore WHEN valid THEN restored`() {
        val id = TemplateId.generate()
        val template = WorkoutTemplate.restore(
            id = id,
            name = "Pull",
            exercises = listOf(TemplateExercise(exerciseId, 0, 4)),
            createdAt = instant,
            updatedAt = instant,
        )
        assertEquals(id, template.id)
    }

    @Test
    fun `GIVEN short template name WHEN create THEN fails`() {
        assertThrows(DomainException::class.java) {
            WorkoutTemplate.create("X", listOf(TemplateExercise(exerciseId, 0, 3)))
        }
    }

    @Test
    fun `GIVEN custom exercise WHEN updateCustom THEN updated fields`() {
        val exercise = Exercise.createCustom("Row", MuscleGroup.BACK, EquipmentType.CABLE) {}
        val updated = exercise.updateCustom(
            name = "Cable Row",
            muscleGroup = MuscleGroup.BACK,
            equipment = EquipmentType.CABLE,
            uniquenessRule = {},
        )
        assertEquals("Cable Row", updated.name)
    }

    @Test
    fun `GIVEN correction without reason WHEN create THEN reason null`() {
        val correction = RecordCorrection.create(
            sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
            originalSetLogId = com.openfitness.domain.valueobject.SetLogId.generate(),
            correctedWeight = com.openfitness.domain.valueobject.Weight.fromKilograms(40.0),
            correctedReps = com.openfitness.domain.valueobject.RepCount(12),
            reason = "   ",
        )
        assertNull(correction.reason)
    }

    @Test
    fun `GIVEN duplicate template orders WHEN create THEN fails`() {
        assertThrows(DomainException::class.java) {
            WorkoutTemplate.create(
                "Bad",
                listOf(
                    TemplateExercise(exerciseId, 0, 3),
                    TemplateExercise(com.openfitness.domain.valueobject.ExerciseId.generate(), 0, 2),
                ),
            )
        }
    }

    @Test
    fun `GIVEN duplicate exercise ids WHEN create template THEN fails`() {
        assertThrows(DomainException::class.java) {
            WorkoutTemplate.create(
                "Dup",
                listOf(
                    TemplateExercise(exerciseId, 0, 3),
                    TemplateExercise(exerciseId, 1, 2),
                ),
            )
        }
    }

    @Test
    fun `GIVEN exercise update with duplicate name THEN fails`() {
        val exercise = Exercise.createCustom("Alpha", MuscleGroup.CHEST, EquipmentType.BARBELL) {}
        val rule = ExerciseNameUniquenessRule()
        assertThrows(com.openfitness.domain.exception.DuplicateExerciseNameException::class.java) {
            exercise.updateCustom(
                name = "Beta",
                muscleGroup = MuscleGroup.CHEST,
                equipment = EquipmentType.BARBELL,
                uniquenessRule = { rule.validate(it, listOf("beta")) },
            )
        }
    }
}
