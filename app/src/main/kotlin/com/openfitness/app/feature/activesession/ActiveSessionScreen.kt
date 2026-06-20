package com.openfitness.app.feature.activesession

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.openfitness.app.R
import com.openfitness.app.common.component.ErrorContent
import com.openfitness.app.common.component.LoadingContent
import com.openfitness.app.common.format.WeightDisplayFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ActiveSessionScreen(
    state: ActiveSessionUiState,
    onEvent: (ActiveSessionEvent) -> Unit,
) {
    val resources = LocalContext.current.resources
    val currentExercise = state.exercises.getOrNull(state.currentExerciseIndex)
    val editingSet = state.editingSetLogId?.let { id -> state.setLogs.firstOrNull { it.id == id } }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = currentExercise?.name ?: stringResource(R.string.active_session_title),
                    )
                },
            )
        },
    ) { padding ->
        when {
            state.isLoading -> LoadingContent(Modifier.padding(padding))
            state.error != null -> ErrorContent(
                error = state.error,
                onRetry = { onEvent(ActiveSessionEvent.Retry) },
                onDismiss = { onEvent(ActiveSessionEvent.Retry) },
                modifier = Modifier.padding(padding),
            )
            state.isCompleted -> Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(24.dp)
                    .testTag("session_summary"),
            ) {
                Text(
                    text = stringResource(R.string.active_session_complete_title),
                    style = MaterialTheme.typography.headlineSmall,
                )
                if (state.newPrCount > 0) {
                    Text(
                        text = stringResource(R.string.pr_new_badge),
                        modifier = Modifier.padding(top = 8.dp),
                    )
                }
            }
            else -> Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                state.restTimerSecondsRemaining?.let { seconds ->
                    Text(text = stringResource(R.string.active_session_rest_timer, seconds))
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = state.weightInput,
                        onValueChange = { onEvent(ActiveSessionEvent.WeightChanged(it)) },
                        label = {
                            Text(WeightDisplayFormatter.weightInputLabel(resources, state.weightUnit))
                        },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("weight_input"),
                    )
                    OutlinedTextField(
                        value = state.repsInput,
                        onValueChange = { onEvent(ActiveSessionEvent.RepsChanged(it)) },
                        label = { Text(stringResource(R.string.active_session_reps)) },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("reps_input"),
                    )
                }
                Button(
                    onClick = { onEvent(ActiveSessionEvent.LogSet) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("log_set_button"),
                ) {
                    Text(stringResource(R.string.active_session_log_set))
                }
                LazyColumn(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    items(state.setLogs, key = { it.id.toString() }) { setLog ->
                        val displayWeight = WeightDisplayFormatter.displayWeightKg(setLog.weightKg, state.weightUnit)
                        Text(
                            text = stringResource(
                                R.string.active_session_set_line,
                                setLog.setNumber,
                                displayWeight ?: 0.0,
                                setLog.reps ?: 0,
                                WeightDisplayFormatter.unitSuffix(state.weightUnit),
                            ),
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { onEvent(ActiveSessionEvent.ShowEditSetDialog(setLog.id)) }
                                .padding(vertical = 4.dp)
                                .testTag("set_log_item"),
                        )
                    }
                }
                Button(
                    onClick = { onEvent(ActiveSessionEvent.ShowFinishDialog) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("finish_workout_button"),
                ) {
                    Text(stringResource(R.string.active_session_finish))
                }
            }
        }
    }

    if (state.showFinishDialog) {
        AlertDialog(
            onDismissRequest = { onEvent(ActiveSessionEvent.DismissFinishDialog) },
            title = { Text(stringResource(R.string.active_session_finish_confirm_title)) },
            confirmButton = {
                TextButton(
                    onClick = { onEvent(ActiveSessionEvent.ConfirmFinish) },
                    modifier = Modifier.testTag("confirm_finish_button"),
                ) {
                    Text(stringResource(R.string.action_confirm))
                }
            },
            dismissButton = {
                TextButton(onClick = { onEvent(ActiveSessionEvent.DismissFinishDialog) }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }

    if (state.showEditSetDialog && editingSet != null) {
        var weight by remember { mutableStateOf(editingSet.weightKg?.toString() ?: "") }
        var reps by remember { mutableStateOf(editingSet.reps?.toString() ?: "") }
        AlertDialog(
            onDismissRequest = { onEvent(ActiveSessionEvent.DismissEditSetDialog) },
            title = { Text(stringResource(R.string.edit_set_title)) },
            text = {
                Column {
                    OutlinedTextField(
                        value = weight,
                        onValueChange = { weight = it },
                        label = {
                            Text(WeightDisplayFormatter.weightInputLabel(resources, state.weightUnit))
                        },
                        modifier = Modifier.testTag("edit_set_weight"),
                    )
                    OutlinedTextField(
                        value = reps,
                        onValueChange = { reps = it },
                        label = { Text(stringResource(R.string.active_session_reps)) },
                        modifier = Modifier.testTag("edit_set_reps"),
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = { onEvent(ActiveSessionEvent.ConfirmEditSet(weight, reps)) },
                    modifier = Modifier.testTag("edit_set_confirm"),
                ) {
                    Text(stringResource(R.string.action_save))
                }
            },
            dismissButton = {
                TextButton(onClick = { onEvent(ActiveSessionEvent.DismissEditSetDialog) }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }
}
