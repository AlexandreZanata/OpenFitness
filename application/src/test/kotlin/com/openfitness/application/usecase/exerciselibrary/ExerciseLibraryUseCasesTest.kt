package com.openfitness.application.usecase.exerciselibrary

import app.cash.turbine.test
import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.domain.model.Exercise
import com.openfitness.domain.repository.ExerciseRepository
import com.openfitness.domain.rule.ExerciseNameUniquenessRule
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.MuscleGroup
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Test

class BrowseExercisesUseCaseTest {

    private val repo: ExerciseRepository = mockk()
    private val useCase = BrowseExercisesUseCase(repo)

    @Test
    fun `GIVEN exercises WHEN invoke THEN filters by query and muscle group`() = runTest {
        val squat = Exercise.restore(
            id = ExerciseId.generate(),
            name = "Back Squat",
            primaryMuscleGroup = MuscleGroup.LEGS,
            equipmentType = EquipmentType.BARBELL,
            isCustom = false,
            createdAt = java.time.Instant.parse("2026-01-01T00:00:00Z"),
        )
        val press = Exercise.restore(
            id = ExerciseId.generate(),
            name = "Bench Press",
            primaryMuscleGroup = MuscleGroup.CHEST,
            equipmentType = EquipmentType.BARBELL,
            isCustom = false,
            createdAt = java.time.Instant.parse("2026-01-01T00:00:00Z"),
        )
        every { repo.observeAll() } returns flowOf(listOf(squat, press))

        useCase("press", MuscleGroup.CHEST).test {
            assertEquals(listOf(press), awaitItem())
            awaitComplete()
        }
    }
}

class CreateCustomExerciseUseCaseTest {

    private val repo: ExerciseRepository = mockk(relaxed = true)
    private val useCase = CreateCustomExerciseUseCase(repo, ExerciseNameUniquenessRule())

    @Test
    fun `GIVEN duplicate name WHEN invoke THEN DuplicateExerciseName`() = runTest {
        coEvery { repo.findAllNames() } returns listOf("Curl")

        val result = useCase("curl", MuscleGroup.BICEPS, EquipmentType.DUMBBELL)

        assertInstanceOf(UseCaseResult.Failure::class.java, result)
        assertInstanceOf(
            AppError.DuplicateExerciseName::class.java,
            (result as UseCaseResult.Failure).error,
        )
    }

    @Test
    fun `GIVEN unique name WHEN invoke THEN saves exercise`() = runTest {
        coEvery { repo.findAllNames() } returns emptyList()

        val result = useCase("Hammer Curl", MuscleGroup.BICEPS, EquipmentType.DUMBBELL)

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        coVerify { repo.save(any()) }
    }
}
