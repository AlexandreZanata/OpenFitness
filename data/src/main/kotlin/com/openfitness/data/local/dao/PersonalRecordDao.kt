package com.openfitness.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.openfitness.data.local.entity.PersonalRecordEntity
import com.openfitness.data.local.entity.PersonalRecordHistoryEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface PersonalRecordDao {
    @Query(
        """
        SELECT * FROM personal_records
        WHERE exercise_id = :exerciseId AND metric = :metric
        LIMIT 1
        """,
    )
    suspend fun findCurrent(exerciseId: String, metric: String): PersonalRecordEntity?

    @Query("SELECT * FROM personal_records ORDER BY achieved_at DESC")
    fun observeAll(): Flow<List<PersonalRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(record: PersonalRecordEntity)

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertHistory(entry: PersonalRecordHistoryEntity)
}

@Dao
interface RecordCorrectionDao {
    @Query("SELECT * FROM record_corrections WHERE session_id = :sessionId ORDER BY created_at ASC")
    suspend fun findBySession(sessionId: String): List<com.openfitness.data.local.entity.RecordCorrectionEntity>

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insert(correction: com.openfitness.data.local.entity.RecordCorrectionEntity)
}
