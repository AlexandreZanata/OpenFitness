package com.openfitness.app.feature.history

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
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
import com.openfitness.app.common.component.EmptyContent
import com.openfitness.app.common.component.ErrorContent
import com.openfitness.app.common.component.LoadingContent
import com.openfitness.app.common.error.toMessage
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    state: HistoryUiState,
    onEvent: (HistoryEvent) -> Unit,
) {
    val resources = LocalContext.current.resources

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = state.lastWorkoutLabel?.let {
                            stringResource(R.string.history_last_workout, it)
                        } ?: stringResource(R.string.history_title),
                    )
                },
            )
        },
    ) { padding ->
        when {
            state.isLoading -> LoadingContent(Modifier.padding(padding))
            state.error != null -> ErrorContent(
                message = state.error.toMessage(resources),
                onRetry = { onEvent(HistoryEvent.Retry) },
                modifier = Modifier.padding(padding),
            )
            state.isEmpty -> EmptyContent(
                title = stringResource(R.string.history_empty_title),
                ctaLabel = stringResource(R.string.history_empty_cta),
                onCtaClick = null,
                modifier = Modifier.padding(padding),
            )
            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .testTag("history_list"),
            ) {
                items(state.sessions, key = { it.id.toString() }) { session ->
                    val dateLabel = session.completedAt?.let { instant ->
                        DateTimeFormatter.ISO_LOCAL_DATE.format(instant.atZone(ZoneId.systemDefault()))
                    } ?: "-"
                    Text(
                        text = stringResource(
                            R.string.history_session_line,
                            dateLabel,
                            session.totalSets,
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onEvent(HistoryEvent.SelectSession(session.id)) }
                            .padding(16.dp),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }
        }
    }

    if (state.showCorrectDialog) {
        var weight by remember { mutableStateOf("") }
        var reps by remember { mutableStateOf("") }
        var reason by remember { mutableStateOf("") }
        AlertDialog(
            onDismissRequest = { onEvent(HistoryEvent.DismissCorrectDialog) },
            title = { Text(stringResource(R.string.correct_record_title)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = weight,
                        onValueChange = { weight = it },
                        label = { Text(stringResource(R.string.active_session_weight)) },
                    )
                    OutlinedTextField(
                        value = reps,
                        onValueChange = { reps = it },
                        label = { Text(stringResource(R.string.active_session_reps)) },
                    )
                    OutlinedTextField(
                        value = reason,
                        onValueChange = { reason = it },
                        label = { Text(stringResource(R.string.correct_record_reason)) },
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = { onEvent(HistoryEvent.ConfirmCorrection(weight, reps, reason)) },
                ) {
                    Text(stringResource(R.string.action_save))
                }
            },
            dismissButton = {
                TextButton(onClick = { onEvent(HistoryEvent.DismissCorrectDialog) }) {
                    Text(stringResource(R.string.action_cancel))
                }
            },
        )
    }
}
