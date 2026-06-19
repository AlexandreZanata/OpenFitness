package com.openfitness.data.repository

import com.openfitness.data.local.dao.WorkoutTemplateDao
import com.openfitness.data.mapper.WorkoutTemplateMapper
import com.openfitness.domain.model.WorkoutTemplate
import com.openfitness.domain.repository.WorkoutTemplateRepository
import com.openfitness.domain.valueobject.TemplateId
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

@Singleton
class WorkoutTemplateRepositoryImpl @Inject constructor(
    private val dao: WorkoutTemplateDao,
) : WorkoutTemplateRepository {

    override suspend fun findById(id: TemplateId): WorkoutTemplate? {
        val entity = dao.findById(id.value.toString()) ?: return null
        val exercises = dao.findExercises(entity.id)
        return WorkoutTemplateMapper.toDomain(entity, exercises)
    }

    override suspend fun save(template: WorkoutTemplate) {
        val (entity, exercises) = WorkoutTemplateMapper.toEntity(template)
        dao.saveTemplate(entity, exercises)
    }

    override suspend fun delete(id: TemplateId) {
        dao.deleteTemplate(id.value.toString())
    }

    override fun observeAll(): Flow<List<WorkoutTemplate>> =
        dao.observeAll().map { templates ->
            templates.map { entity ->
                WorkoutTemplateMapper.toDomain(entity, emptyList())
            }
        }
}
