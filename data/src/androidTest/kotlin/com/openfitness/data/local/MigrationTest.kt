package com.openfitness.data.local

import androidx.room.Room
import androidx.room.testing.MigrationTestHelper
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MigrationTest {

    private val testDb = "migration-test"

    @get:Rule
    val helper: MigrationTestHelper = MigrationTestHelper(
        InstrumentationRegistry.getInstrumentation(),
        OpenFitnessDatabase::class.java,
        emptyList(),
        FrameworkSQLiteOpenHelperFactory(),
    )

    @Test
    fun createAndOpenV1Database() {
        helper.createDatabase(testDb, 1).close()

        Room.databaseBuilder(
            InstrumentationRegistry.getInstrumentation().targetContext,
            OpenFitnessDatabase::class.java,
            testDb,
        ).build().apply {
            openHelper.writableDatabase.close()
            close()
        }
    }
}
