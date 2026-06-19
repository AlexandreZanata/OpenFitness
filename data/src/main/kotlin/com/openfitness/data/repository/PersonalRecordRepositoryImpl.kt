package com.openfitness.data.repository

import com.openfitness.data.local.dao.PersonalRecordDao
import com.openfitness.data.local.dao.RecordCorrectionDao
import com.openfitness.data.mapper.PersonalRecordMapper
import com.openfitness.data.mapper.RecordCorrectionMapper
import com.openfitness.domain.model.PersonalRecord
import com.openfitness.domain.model.PersonalRecordHistoryEntry
import com.openfitness.domain.model.RecordCorrection
import com.openfitness.domain.repository.PersonalRecordRepository
import com.openfitness.domain.repository.RecordCorrectionRepository
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.PersonalRecordMetric
import com.openfitness.domain.valueobject.SessionId
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

@Singleton
class PersonalRecordRepositoryImpl @Inject constructor(
    private val dao: PersonalRecordDao,
) : PersonalRecordRepository {

    override suspend fun findCurrent(
        exerciseId: ExerciseId,
        metric: PersonalRecordMetric,
    ): PersonalRecord? = dao.findCurrent(exerciseId.toString(), metric.name)?.let(PersonalRecordMapper::toDomain)

    override suspend fun save(record: PersonalRecord) {
        dao.upsert(PersonalRecordMapper.toEntity(record))
    }

    override suspend fun saveHistory(entry: PersonalRecordHistoryEntry) {
        dao.insertHistory(PersonalRecordMapper.historyToEntity(entry))
    }

    override fun observeAll(): Flow<List<PersonalRecord>> =
        dao.observeAll().map { records -> records.map(PersonalRecordMapper::toDomain) }
}

@Singleton
class RecordCorrectionRepositoryImpl @Inject constructor(
    private val dao: RecordCorrectionDao,
) : RecordCorrectionRepository {

    override suspend fun findBySession(sessionId: SessionId): List<RecordCorrection> =
        dao.findBySession(sessionId.toString()).map(RecordCorrectionMapper::toDomain)

    override suspend fun save(correction: RecordCorrection) {
        dao.insert(RecordCorrectionMapper.toEntity(correction))
    }
}
