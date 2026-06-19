package com.openfitness.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.openfitness.data.local.entity.SessionExerciseEntity
import com.openfitness.data.local.entity.SetLogEntity
import com.openfitness.data.local.entity.WorkoutSessionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface WorkoutSessionDao {
    @Query("SELECT * FROM workout_sessions WHERE id = :id LIMIT 1")
    suspend fun findById(id: String): WorkoutSessionEntity?

    @Query("SELECT * FROM workout_sessions WHERE status = 'IN_PROGRESS' LIMIT 1")
    suspend fun findInProgress(): WorkoutSessionEntity?

    @Query(
        """
        SELECT * FROM workout_sessions
        WHERE status = 'COMPLETED'
        ORDER BY completed_at DESC
        LIMIT :limit
        """,
    )
    fun observeCompleted(limit: Int): Flow<List<WorkoutSessionEntity>>

    @Query("SELECT * FROM session_exercises WHERE session_id = :sessionId ORDER BY order_index ASC")
    suspend fun findSessionExercises(sessionId: String): List<SessionExerciseEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertSession(session: WorkoutSessionEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertSessionExercises(exercises: List<SessionExerciseEntity>)

    @Query("DELETE FROM session_exercises WHERE session_id = :sessionId")
    suspend fun deleteSessionExercises(sessionId: String)

    @Transaction
    suspend fun saveSession(
        session: WorkoutSessionEntity,
        exercises: List<SessionExerciseEntity>,
    ) {
        upsertSession(session)
        deleteSessionExercises(session.id)
        if (exercises.isNotEmpty()) {
            upsertSessionExercises(exercises)
        }
    }
}

@Dao
interface SetLogDao {
    @Query("SELECT * FROM set_logs WHERE session_id = :sessionId ORDER BY completed_at ASC")
    suspend fun findBySession(sessionId: String): List<SetLogEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(setLog: SetLogEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(setLogs: List<SetLogEntity>)

    @Query(
        """
        SELECT s.status FROM workout_sessions s
        INNER JOIN set_logs l ON l.session_id = s.id
        WHERE l.id = :setLogId
        LIMIT 1
        """,
    )
    suspend fun sessionStatusForSetLog(setLogId: String): String?
}
