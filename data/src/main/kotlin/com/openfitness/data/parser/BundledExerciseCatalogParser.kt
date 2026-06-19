package com.openfitness.data.parser

import com.openfitness.domain.model.Exercise
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.MuscleGroup
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant

data class CatalogExerciseEntry(
    val name: String,
    val muscleGroup: MuscleGroup,
    val equipmentType: EquipmentType,
)

class BundledExerciseCatalogParser {
    fun parse(json: String, parsedAt: Instant = Instant.now()): List<Exercise> {
        val array = JSONArray(json)
        return buildList {
            for (index in 0 until array.length()) {
                add(parseEntry(array.getJSONObject(index), parsedAt))
            }
        }
    }

    private fun parseEntry(item: JSONObject, parsedAt: Instant): Exercise {
        val name = item.getString("name").trim()
        val muscleGroup = MuscleGroup.valueOf(item.getString("primaryMuscleGroup"))
        val equipmentType = EquipmentType.valueOf(item.getString("equipmentType"))
        return Exercise.restore(
            id = com.openfitness.domain.valueobject.ExerciseId.generate(),
            name = name,
            primaryMuscleGroup = muscleGroup,
            equipmentType = equipmentType,
            isCustom = false,
            createdAt = parsedAt,
        )
    }
}
