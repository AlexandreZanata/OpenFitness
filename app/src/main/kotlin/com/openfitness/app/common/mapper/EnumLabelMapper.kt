package com.openfitness.app.common.mapper

import androidx.annotation.StringRes
import com.openfitness.app.R
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.MuscleGroup

@StringRes
fun MuscleGroup.labelRes(): Int = when (this) {
    MuscleGroup.CHEST -> R.string.muscle_group_chest
    MuscleGroup.BACK -> R.string.muscle_group_back
    MuscleGroup.SHOULDERS -> R.string.muscle_group_shoulders
    MuscleGroup.BICEPS -> R.string.muscle_group_biceps
    MuscleGroup.TRICEPS -> R.string.muscle_group_triceps
    MuscleGroup.LEGS -> R.string.muscle_group_legs
    MuscleGroup.CORE -> R.string.muscle_group_core
    MuscleGroup.FULL_BODY -> R.string.muscle_group_full_body
    MuscleGroup.CARDIO -> R.string.muscle_group_cardio
}

@StringRes
fun EquipmentType.labelRes(): Int = when (this) {
    EquipmentType.BARBELL -> R.string.equipment_barbell
    EquipmentType.DUMBBELL -> R.string.equipment_dumbbell
    EquipmentType.MACHINE -> R.string.equipment_machine
    EquipmentType.CABLE -> R.string.equipment_cable
    EquipmentType.BODYWEIGHT -> R.string.equipment_bodyweight
    EquipmentType.OTHER -> R.string.equipment_other
}
