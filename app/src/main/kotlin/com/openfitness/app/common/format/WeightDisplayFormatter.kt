package com.openfitness.app.common.format

import android.content.res.Resources
import com.openfitness.app.R

object WeightDisplayFormatter {

    private const val KG_TO_LB = 2.20462

    fun isPounds(unit: String): Boolean = unit.equals("lb", ignoreCase = true)

    fun weightInputLabel(resources: Resources, unit: String): String =
        if (isPounds(unit)) {
            resources.getString(R.string.active_session_weight_lb)
        } else {
            resources.getString(R.string.active_session_weight_kg)
        }

    fun unitSuffix(unit: String): String =
        if (isPounds(unit)) {
            "lb"
        } else {
            "kg"
        }

    fun displayWeightKg(kg: Double?, unit: String): Double? {
        if (kg == null) return null
        return if (isPounds(unit)) kg * KG_TO_LB else kg
    }
}
