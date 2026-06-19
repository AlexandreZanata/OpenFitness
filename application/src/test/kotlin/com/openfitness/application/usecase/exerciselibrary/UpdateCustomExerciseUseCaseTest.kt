package com.openfitness.application.usecase.exerciselibrary

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
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Test
import java.time.Instant

class UpdateCustomExerciseUseCaseTest {

    private val repo: ExerciseRepository = mockk(relaxed = true)
    private val useCase = UpdateCustomExerciseUseCase(repo, ExerciseNameUniquenessRule())

    @Test
    fun `GIVEN missing exercise WHEN invoke THEN NotFound`() = runTest {
        val id = ExerciseId.generate()
        coEvery { repo.findById(id) } returns null

        val result = useCase(id, "Curl", MuscleGroup.BICEPS, EquipmentType.DUMBBELL)

        assertEquals(AppError.NotFound, (result as UseCaseResult.Failure).error)
    }

    @Test
    fun `GIVEN custom exercise WHEN invoke THEN updates and saves`() = runTest {
        val exercise = Exercise.createCustom("Old Curl", MuscleGroup.BICEPS, EquipmentType.DUMBBELL) {}
        coEvery { repo.findById(exercise.id) } returns exercise
        coEvery { repo.findAllNames() } returns listOf("Old Curl")

        val result = useCase(exercise.id, "New Curl", MuscleGroup.BICEPS, EquipmentType.DUMBBELL)

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        assertEquals("New Curl", (result as UseCaseResult.Success).value.name)
        coVerify { repo.save(any()) }
    }
}
