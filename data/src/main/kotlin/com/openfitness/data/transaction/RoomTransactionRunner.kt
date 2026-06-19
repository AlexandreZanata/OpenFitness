package com.openfitness.data.transaction

import androidx.room.withTransaction
import com.openfitness.data.local.OpenFitnessDatabase
import com.openfitness.domain.repository.TransactionRunner
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RoomTransactionRunner @Inject constructor(
    private val database: OpenFitnessDatabase,
) : TransactionRunner {

    override suspend fun <T> run(block: suspend () -> T): T =
        database.withTransaction { block() }
}
