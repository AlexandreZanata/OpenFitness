package com.openfitness.data.mapper

import com.openfitness.data.local.entity.ExerciseEntity
import com.openfitness.data.local.entity.PersonalRecordEntity
import com.openfitness.data.local.entity.PersonalRecordHistoryEntity
import com.openfitness.data.local.entity.RecordCorrectionEntity
import com.openfitness.data.local.entity.SessionExerciseEntity
import com.openfitness.data.local.entity.SetLogEntity
import com.openfitness.data.local.entity.TemplateExerciseEntity
import com.openfitness.data.local.entity.WorkoutSessionEntity
import com.openfitness.data.local.entity.WorkoutTemplateEntity
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.model.PersonalRecord
import com.openfitness.domain.model.PersonalRecordHistoryEntry
import com.openfitness.domain.model.RecordCorrection
import com.openfitness.domain.model.SessionExercise
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.TemplateExercise
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.model.WorkoutTemplate
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.RepCount
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SessionStatus
import com.openfitness.domain.valueobject.SetLogId
import com.openfitness.domain.valueobject.TemplateId
import com.openfitness.domain.valueobject.Weight
import java.time.Instant

object ExerciseMapper {
    fun toEntity(exercise: Exercise): ExerciseEntity = ExerciseEntity(
        id = exercise.id.toString(),
        name = exercise.name,
        primaryMuscleGroup = exercise.primaryMuscleGroup.name,
        equipmentType = exercise.equipmentType.name,
        isCustom = exercise.isCustom,
        createdAt = exercise.createdAt.toEpochMilli(),
    )

    fun toDomain(entity: ExerciseEntity): Exercise = Exercise.restore(
        id = ExerciseId.fromString(entity.id),
        name = entity.name,
        primaryMuscleGroup = MuscleGroup.valueOf(entity.primaryMuscleGroup),
        equipmentType = EquipmentType.valueOf(entity.equipmentType),
        isCustom = entity.isCustom,
        createdAt = Instant.ofEpochMilli(entity.createdAt),
    )
}

object WorkoutTemplateMapper {
    fun toEntity(template: WorkoutTemplate): Pair<WorkoutTemplateEntity, List<TemplateExerciseEntity>> {
        val entity = WorkoutTemplateEntity(
            id = template.id.value.toString(),
            name = template.name,
            createdAt = template.createdAt.toEpochMilli(),
            updatedAt = template.updatedAt.toEpochMilli(),
        )
        val exercises = template.exercises.map {
            TemplateExerciseEntity(
                templateId = template.id.value.toString(),
                exerciseId = it.exerciseId.toString(),
                orderIndex = it.order,
                targetSets = it.targetSets,
                targetReps = it.targetReps?.value,
                targetWeightKg = it.targetWeight?.kilograms,
            )
        }
        return entity to exercises
    }

    fun toDomain(
        entity: WorkoutTemplateEntity,
        exercises: List<TemplateExerciseEntity>,
    ): WorkoutTemplate = WorkoutTemplate.restore(
        id = TemplateId.fromString(entity.id),
        name = entity.name,
        exercises = exercises.map {
            TemplateExercise(
                exerciseId = ExerciseId.fromString(it.exerciseId),
                order = it.orderIndex,
                targetSets = it.targetSets,
                targetReps = it.targetReps?.let(::RepCount),
                targetWeight = it.targetWeightKg?.let(Weight::fromKilograms),
            )
        },
        createdAt = Instant.ofEpochMilli(entity.createdAt),
        updatedAt = Instant.ofEpochMilli(entity.updatedAt),
    )
}

object WorkoutSessionMapper {
    fun toEntity(session: WorkoutSession): Pair<WorkoutSessionEntity, List<SessionExerciseEntity>> {
        val entity = WorkoutSessionEntity(
            id = session.id.toString(),
            templateId = session.templateId?.value?.toString(),
            status = session.status.name,
            startedAt = session.startedAt?.toEpochMilli(),
            completedAt = session.completedAt?.toEpochMilli(),
            cancelledAt = session.cancelledAt?.toEpochMilli(),
        )
        val exercises = session.exercises.map {
            SessionExerciseEntity(
                sessionId = session.id.toString(),
                exerciseId = it.exerciseId.toString(),
                orderIndex = it.order,
            )
        }
        return entity to exercises
    }

    fun toDomain(
        entity: WorkoutSessionEntity,
        exercises: List<SessionExerciseEntity>,
        setLogs: List<SetLog>,
    ): WorkoutSession = WorkoutSession.restore(
        id = SessionId.fromString(entity.id),
        templateId = entity.templateId?.let(TemplateId::fromString),
        status = SessionStatus.valueOf(entity.status),
        exercises = exercises.map {
            SessionExercise(
                exerciseId = ExerciseId.fromString(it.exerciseId),
                order = it.orderIndex,
            )
        },
        setLogs = setLogs,
        startedAt = entity.startedAt?.let(Instant::ofEpochMilli),
        completedAt = entity.completedAt?.let(Instant::ofEpochMilli),
        cancelledAt = entity.cancelledAt?.let(Instant::ofEpochMilli),
    )
}

object SetLogMapper {
    fun toEntity(setLog: SetLog): SetLogEntity = SetLogEntity(
        id = setLog.id.value.toString(),
        sessionId = setLog.sessionId.toString(),
        exerciseId = setLog.exerciseId.toString(),
        setNumber = setLog.setNumber,
        weightKg = setLog.weight?.kilograms,
        reps = setLog.reps?.value,
        completedAt = setLog.completedAt.toEpochMilli(),
    )

    fun toDomain(entity: SetLogEntity): SetLog = SetLog(
        id = SetLogId.fromString(entity.id),
        sessionId = SessionId.fromString(entity.sessionId),
        exerciseId = ExerciseId.fromString(entity.exerciseId),
        setNumber = entity.setNumber,
        weight = entity.weightKg?.let(Weight::fromKilograms),
        reps = entity.reps?.let(::RepCount),
        completedAt = Instant.ofEpochMilli(entity.completedAt),
    )
}

object PersonalRecordMapper {
    fun toEntity(record: PersonalRecord): PersonalRecordEntity = PersonalRecordEntity(
        exerciseId = record.exerciseId.toString(),
        metric = record.metric.name,
        value = record.value,
        achievedAt = record.achievedAt.toEpochMilli(),
        sessionId = record.sessionId.toString(),
        setLogId = record.setLogId.value.toString(),
    )

    fun toDomain(entity: PersonalRecordEntity): PersonalRecord = PersonalRecord(
        exerciseId = ExerciseId.fromString(entity.exerciseId),
        metric = PersonalRecordMetric.valueOf(entity.metric),
        value = entity.value,
        achievedAt = Instant.ofEpochMilli(entity.achievedAt),
        sessionId = SessionId.fromString(entity.sessionId),
        setLogId = SetLogId.fromString(entity.setLogId),
    )

    fun historyToEntity(entry: PersonalRecordHistoryEntry): PersonalRecordHistoryEntity =
        PersonalRecordHistoryEntity(
            id = entry.id,
            exerciseId = entry.exerciseId.toString(),
            metric = entry.metric.name,
            value = entry.value,
            achievedAt = entry.achievedAt.toEpochMilli(),
            sessionId = entry.sessionId.toString(),
            setLogId = entry.setLogId.value.toString(),
            supersededAt = entry.supersededAt.toEpochMilli(),
        )
}

object RecordCorrectionMapper {
    fun toEntity(correction: RecordCorrection): RecordCorrectionEntity = RecordCorrectionEntity(
        id = correction.id,
        sessionId = correction.sessionId.toString(),
        originalSetLogId = correction.originalSetLogId.value.toString(),
        correctedWeightKg = correction.correctedWeight?.kilograms,
        correctedReps = correction.correctedReps?.value,
        reason = correction.reason,
        createdAt = correction.createdAt.toEpochMilli(),
    )

    fun toDomain(entity: RecordCorrectionEntity): RecordCorrection = RecordCorrection(
        id = entity.id,
        sessionId = SessionId.fromString(entity.sessionId),
        originalSetLogId = SetLogId.fromString(entity.originalSetLogId),
        correctedWeight = entity.correctedWeightKg?.let(Weight::fromKilograms),
        correctedReps = entity.correctedReps?.let(::RepCount),
        reason = entity.reason,
        createdAt = Instant.ofEpochMilli(entity.createdAt),
    )
}
