package com.openfitness.app

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextReplacement
import androidx.compose.ui.test.performTextInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class WorkoutFlowUiTest {

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun happyPath_startLogComplete() {
        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("start_quick_workout").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("start_quick_workout").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("weight_input").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("weight_input").performTextInput("60")
        composeRule.onNodeWithTag("reps_input").performTextInput("8")
        composeRule.onNodeWithTag("log_set_button").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("set_log_item").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("finish_workout_button").performClick()
        composeRule.onNodeWithTag("confirm_finish_button").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("session_summary").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithText("Workout complete").assertIsDisplayed()
    }

    @Test
    fun editSetDuringActiveSession() {
        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("start_quick_workout").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("start_quick_workout").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("weight_input").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("weight_input").performTextInput("50")
        composeRule.onNodeWithTag("reps_input").performTextInput("10")
        composeRule.onNodeWithTag("log_set_button").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("set_log_item").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("set_log_item").performClick()

        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule.onAllNodesWithTag("edit_set_confirm").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("edit_set_weight").performTextReplacement("55")
        composeRule.onNodeWithTag("edit_set_reps").performTextReplacement("12")
        composeRule.onNodeWithTag("edit_set_confirm").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithText("55.0").fetchSemanticsNodes().isNotEmpty()
        }
    }
}
