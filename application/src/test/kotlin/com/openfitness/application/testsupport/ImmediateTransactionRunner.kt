package com.openfitness.application.testsupport

import com.openfitness.domain.repository.TransactionRunner

class ImmediateTransactionRunner : TransactionRunner {
    override suspend fun <T> run(block: suspend () -> T): T = block()
}
