package com.openfitness.app

import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
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

    private fun startQuickWorkout() {
        composeRule.waitUntil(timeoutMillis = 20_000) {
            composeRule.onAllNodesWithTag("start_quick_workout", useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
        composeRule.onNodeWithTag("start_quick_workout", useUnmergedTree = true)
            .assertHasClickAction()
            .performClick()
        composeRule.waitForIdle()
        composeRule.waitUntil(timeoutMillis = 20_000) {
            composeRule.onAllNodesWithTag("weight_input", useUnmergedTree = true)
                .fetchSemanticsNodes()
                .isNotEmpty()
        }
    }

    private fun logFirstSet(weight: String, reps: String) {
        composeRule.onNodeWithTag("weight_input").performTextInput(weight)
        composeRule.onNodeWithTag("reps_input").performTextInput(reps)
        composeRule.onNodeWithTag("log_set_button").performClick()
        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("set_log_item").fetchSemanticsNodes().isNotEmpty()
        }
    }

    private fun finishWorkout() {
        composeRule.onNodeWithTag("finish_workout_button").performClick()
        composeRule.onNodeWithTag("confirm_finish_button").performClick()
        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("session_summary").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun happyPath_startLogComplete() {
        startQuickWorkout()
        logFirstSet("60", "8")
        finishWorkout()
        composeRule.onNodeWithTag("session_summary").assertIsDisplayed()
    }

    @Test
    fun editSetDuringActiveSession() {
        startQuickWorkout()
        logFirstSet("50", "10")

        composeRule.onNodeWithTag("set_log_item").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("edit_set_confirm").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("edit_set_weight").performTextReplacement("55")
        composeRule.onNodeWithTag("edit_set_reps").performTextReplacement("12")
        composeRule.onNodeWithTag("edit_set_confirm").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("edit_set_confirm").fetchSemanticsNodes().isEmpty()
        }

        composeRule.onNode(hasTestTag("set_log_item") and hasText("55", substring = true)).assertExists()
        composeRule.onNode(hasTestTag("set_log_item") and hasText("12", substring = true)).assertExists()

        finishWorkout()
    }

    @Test
    fun correctCompletedSet_appendsCorrectionInHistory() {
        startQuickWorkout()
        logFirstSet("50", "10")
        finishWorkout()

        composeRule.activityRule.scenario.onActivity { activity ->
            activity.onBackPressedDispatcher.onBackPressed()
        }

        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("nav_history").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("nav_history").performClick()

        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("history_session_item").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onAllNodesWithTag("history_session_item", useUnmergedTree = true)[0].performClick()

        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("history_session_detail").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("correct_set_button").performClick()

        composeRule.waitUntil(timeoutMillis = 10_000) {
            composeRule.onAllNodesWithTag("correct_record_confirm").fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithTag("correct_record_weight").performTextReplacement("55")
        composeRule.onNodeWithTag("correct_record_reps").performTextReplacement("12")
        composeRule.onNodeWithTag("correct_record_confirm").performClick()

        composeRule.waitUntil(timeoutMillis = 15_000) {
            composeRule.onAllNodesWithTag("history_correction_item").fetchSemanticsNodes().isNotEmpty()
        }
    }
}
