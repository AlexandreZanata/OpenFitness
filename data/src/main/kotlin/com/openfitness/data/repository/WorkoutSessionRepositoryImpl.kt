package com.openfitness.data.repository

import androidx.room.withTransaction
import com.openfitness.data.local.OpenFitnessDatabase
import com.openfitness.data.local.dao.SetLogDao
import com.openfitness.data.local.dao.WorkoutSessionDao
import com.openfitness.data.mapper.SetLogMapper
import com.openfitness.data.mapper.WorkoutSessionMapper
import com.openfitness.domain.exception.ImmutableRecordException
import com.openfitness.domain.model.SetLog
import com.openfitness.domain.model.WorkoutSession
import com.openfitness.domain.repository.SetLogRepository
import com.openfitness.domain.repository.WorkoutSessionRepository
import com.openfitness.domain.valueobject.SessionId
import com.openfitness.domain.valueobject.SessionStatus
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map

@Singleton
class WorkoutSessionRepositoryImpl @Inject constructor(
    private val database: OpenFitnessDatabase,
    private val sessionDao: WorkoutSessionDao,
    private val setLogDao: SetLogDao,
) : WorkoutSessionRepository {

    override suspend fun findById(id: SessionId): WorkoutSession? = loadSession(id.toString())

    override suspend fun findInProgress(): WorkoutSession? =
        sessionDao.findInProgress()?.let { loadSession(it.id) }

    override suspend fun save(session: WorkoutSession) {
        val existing = sessionDao.findById(session.id.toString())
        if (existing?.status == SessionStatus.COMPLETED.name) {
            throw ImmutableRecordException("Completed workout sessions cannot be modified")
        }
        database.withTransaction {
            val (entity, exercises) = WorkoutSessionMapper.toEntity(session)
            sessionDao.saveSession(entity, exercises)
            session.setLogs.forEach { setLog ->
                setLogDao.upsert(SetLogMapper.toEntity(setLog))
            }
        }
    }

    override fun observeCompleted(limit: Int): Flow<List<WorkoutSession>> = flow {
        sessionDao.observeCompleted(limit).collect { sessions ->
            emit(sessions.mapNotNull { loadSession(it.id) })
        }
    }

    private suspend fun loadSession(id: String): WorkoutSession? {
        val entity = sessionDao.findById(id) ?: return null
        val exercises = sessionDao.findSessionExercises(id)
        val setLogs = setLogDao.findBySession(id).map(SetLogMapper::toDomain)
        return WorkoutSessionMapper.toDomain(entity, exercises, setLogs)
    }
}

@Singleton
class SetLogRepositoryImpl @Inject constructor(
    private val setLogDao: SetLogDao,
    private val sessionDao: WorkoutSessionDao,
) : SetLogRepository {

    override suspend fun findBySession(sessionId: SessionId): List<SetLog> =
        setLogDao.findBySession(sessionId.toString()).map(SetLogMapper::toDomain)

    override suspend fun save(setLog: SetLog) {
        ensureMutable(setLog.sessionId)
        setLogDao.upsert(SetLogMapper.toEntity(setLog))
    }

    override suspend fun saveAll(setLogs: List<SetLog>) {
        if (setLogs.isEmpty()) return
        ensureMutable(setLogs.first().sessionId)
        setLogDao.upsertAll(setLogs.map(SetLogMapper::toEntity))
    }

    private suspend fun ensureMutable(sessionId: SessionId) {
        val session = sessionDao.findById(sessionId.toString())
            ?: throw ImmutableRecordException("Session not found")
        if (session.status == SessionStatus.COMPLETED.name) {
            throw ImmutableRecordException("Cannot modify set logs of a completed session")
        }
    }
}
