package com.openfitness.domain.model

import com.openfitness.domain.event.SetLogged
import com.openfitness.domain.event.SetLogUpdated
import com.openfitness.domain.event.WorkoutSessionStarted
import com.openfitness.domain.exception.DomainException
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.rule.ExerciseNameUniquenessRule
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionStatus
import com.openfitness.domain.valueobject.Weight
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Test
import java.time.Instant

class ExerciseTest {

    @Test
    fun `GIVEN blank name WHEN createCustom THEN DomainException`() {
        assertThrows(DomainException::class.java) {
            Exercise.createCustom(" ", MuscleGroup.CHEST, EquipmentType.BARBELL) {}
        }
    }

    @Test
    fun `GIVEN bundled exercise WHEN rename THEN ImmutableRecordException`() {
        val bundled = Exercise.restore(
            id = ExerciseId.generate(),
            name = "Squat",
            primaryMuscleGroup = MuscleGroup.LEGS,
            equipmentType = EquipmentType.BARBELL,
            isCustom = false,
            createdAt = Instant.parse("2026-01-01T00:00:00Z"),
        )
        assertThrows(com.openfitness.domain.exception.ImmutableRecordException::class.java) {
            Exercise.rename(bundled, "New Squat") {}
        }
    }

    @Test
    fun `GIVEN custom exercise WHEN rename unique THEN accepted`() {
        val custom = Exercise.createCustom("My Squat", MuscleGroup.LEGS, EquipmentType.BARBELL) {}
        val renamed = Exercise.rename(custom, "My Squat Pro") {}
        assertEquals("My Squat Pro", renamed.name)
    }
}

class WorkoutSessionTest {

    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T10:00:00Z")

    private fun plannedSession(): WorkoutSession = WorkoutSession.create(
        templateId = null,
        exercises = listOf(SessionExercise(exerciseId, 0)),
    )

    @Test
    fun `GIVEN PLANNED session WHEN start THEN WorkoutSessionStarted emitted`() {
        val started = plannedSession().start(instant)
        assertEquals(SessionStatus.IN_PROGRESS, started.status)
        assertInstanceOf(WorkoutSessionStarted::class.java, started.events.first())
    }

    @Test
    fun `GIVEN IN_PROGRESS WHEN logSet THEN SetLogged emitted`() {
        val session = plannedSession().start(instant)
        val setLog = SetLog.create(session.id, exerciseId, 1, Weight.fromKilograms(50.0), RepCount(10), instant)
        val updated = session.logSet(setLog)
        assertEquals(1, updated.setLogs.size)
        assertInstanceOf(SetLogged::class.java, updated.events.last())
    }

    @Test
    fun `GIVEN COMPLETED session WHEN logSet THEN ImmutableRecordException`() {
        val session = plannedSession()
        val setLog = SetLog.create(session.id, exerciseId, 1, Weight.fromKilograms(50.0), RepCount(10), instant)
        val completed = session.start(instant).logSet(setLog).complete(instant)
        assertThrows(ImmutableRecordException::class.java) {
            completed.logSet(setLog)
        }
    }

    @Test
    fun `GIVEN IN_PROGRESS WHEN updateSetLog THEN SetLogUpdated emitted`() {
        val session = plannedSession().start(instant)
        val setLog = SetLog.create(session.id, exerciseId, 1, Weight.fromKilograms(50.0), RepCount(10), instant)
        val withSet = session.logSet(setLog).consumeEvents()
        val updated = session.logSet(setLog).updateSetLog(
            setLog.id,
            Weight.fromKilograms(55.0),
            RepCount(8),
            instant.plusSeconds(60),
        )
        assertEquals(55.0, updated.setLogs.first().weight?.kilograms)
        assertInstanceOf(SetLogUpdated::class.java, updated.events.last())
    }

    @Test
    fun `GIVEN COMPLETED session WHEN updateSetLog THEN ImmutableRecordException BR-008`() {
        val session = plannedSession()
        val setLog = SetLog.create(session.id, exerciseId, 1, Weight.fromKilograms(50.0), RepCount(10), instant)
        val completed = session.start(instant).logSet(setLog).complete(instant)
        assertThrows(ImmutableRecordException::class.java) {
            completed.updateSetLog(setLog.id, Weight.fromKilograms(60.0), RepCount(10), instant)
        }
    }
}

class SetLogTest {

    @Test
    fun `GIVEN no weight and no reps WHEN create THEN fails BR-004`() {
        assertThrows(DomainException::class.java) {
            SetLog.create(
                sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
                exerciseId = ExerciseId.generate(),
                setNumber = 1,
                weight = null,
                reps = null,
                completedAt = Instant.now(),
            )
        }
    }
}

class WorkoutTemplateTest {

    @Test
    fun `GIVEN zero exercises WHEN create THEN fails BR-003`() {
        assertThrows(DomainException::class.java) {
            WorkoutTemplate.create("Leg Day", emptyList())
        }
    }
}

class PersonalRecordTest {

    @Test
    fun `GIVEN equal value WHEN tryUpdate THEN NoChange`() {
        val aggregate = PersonalRecordAggregate(
            PersonalRecord(
                exerciseId = ExerciseId.generate(),
                metric = com.openfitness.domain.valueobject.PersonalRecordMetric.MAX_WEIGHT,
                value = 100.0,
                achievedAt = Instant.now(),
                sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
                setLogId = com.openfitness.domain.valueobject.SetLogId.generate(),
            ),
        )
        val result = aggregate.tryUpdate(
            PersonalRecordCandidate(
                exerciseId = ExerciseId.generate(),
                metric = com.openfitness.domain.valueobject.PersonalRecordMetric.MAX_WEIGHT,
                value = 100.0,
                sessionId = com.openfitness.domain.valueobject.SessionId.generate(),
                setLogId = com.openfitness.domain.valueobject.SetLogId.generate(),
                achievedAt = Instant.now(),
            ),
        )
        assertInstanceOf(PersonalRecordUpdateResult.NoChange::class.java, result)
    }
}
