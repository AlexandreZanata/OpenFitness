package com.openfitness.application.usecase.template

import com.openfitness.application.error.AppError
import com.openfitness.application.error.UseCaseResult
import com.openfitness.application.model.TemplateExerciseInput
import com.openfitness.domain.model.TemplateExercise
import com.openfitness.domain.model.WorkoutTemplate
import com.openfitness.domain.repository.WorkoutTemplateRepository
import com.openfitness.domain.valueobject.ExerciseId
import com.openfitness.domain.valueobject.TemplateId
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import app.cash.turbine.test
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Test
import java.time.Instant

class TemplateUseCasesTest {

    private val repo: WorkoutTemplateRepository = mockk(relaxed = true)
    private val exerciseId = ExerciseId.generate()
    private val instant = Instant.parse("2026-06-19T10:00:00Z")

    @Test
    fun `GIVEN templates WHEN list THEN emits from repository`() = runTest {
        val template = WorkoutTemplate.create(
            name = "Push Day",
            exercises = listOf(TemplateExercise(exerciseId, 0, 3)),
            createdAt = instant,
        )
        every { repo.observeAll() } returns flowOf(listOf(template))

        ListWorkoutTemplatesUseCase(repo)().test {
            assertEquals(listOf(template), awaitItem())
            awaitComplete()
        }
    }

    @Test
    fun `GIVEN valid input WHEN create template THEN saves`() = runTest {
        val useCase = CreateWorkoutTemplateUseCase(repo)
        val input = listOf(TemplateExerciseInput(exerciseId, targetSets = 3))

        val result = useCase("Push Day", input)

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        coVerify { repo.save(any()) }
    }

    @Test
    fun `GIVEN missing template WHEN update THEN NotFound`() = runTest {
        val useCase = UpdateWorkoutTemplateUseCase(repo)
        val id = TemplateId.generate()
        coEvery { repo.findById(id) } returns null

        val result = useCase(id, name = "Updated", exercises = null)

        assertEquals(AppError.NotFound, (result as UseCaseResult.Failure).error)
    }

    @Test
    fun `GIVEN existing template WHEN update name THEN saves renamed template`() = runTest {
        val useCase = UpdateWorkoutTemplateUseCase(repo)
        val template = WorkoutTemplate.create(
            name = "Leg Day",
            exercises = listOf(TemplateExercise(exerciseId, 0, 4)),
            createdAt = instant,
        )
        coEvery { repo.findById(template.id) } returns template

        val result = useCase(template.id, name = "Heavy Leg Day", exercises = null)

        assertInstanceOf(UseCaseResult.Success::class.java, result)
        assertEquals("Heavy Leg Day", (result as UseCaseResult.Success).value.name)
        coVerify { repo.save(any()) }
    }
}
