package com.openfitness.app.feature.history

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.ui.Alignment
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
    val showingDetail = state.selectedSessionId != null

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = when {
                            showingDetail -> stringResource(R.string.history_detail_title)
                            state.lastWorkoutLabel != null -> stringResource(
                                R.string.history_last_workout,
                                state.lastWorkoutLabel,
                            )
                            else -> stringResource(R.string.history_title)
                        },
                    )
                },
                navigationIcon = {
                    if (showingDetail) {
                        IconButton(
                            onClick = { onEvent(HistoryEvent.DismissDetail) },
                            modifier = Modifier.testTag("history_detail_back"),
                        ) {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = stringResource(R.string.action_back),
                            )
                        }
                    }
                },
            )
        },
    ) { padding ->
        when {
            state.isLoading -> LoadingContent(Modifier.padding(padding))
            state.error != null && !showingDetail -> ErrorContent(
                message = state.error.toMessage(resources),
                onRetry = { onEvent(HistoryEvent.Retry) },
                modifier = Modifier.padding(padding),
            )
            showingDetail -> SessionDetailContent(
                detail = state.selectedSessionDetail,
                isLoading = state.isLoadingDetail,
                error = state.error,
                onCorrect = { setLogId -> onEvent(HistoryEvent.ShowCorrectDialog(setLogId)) },
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
                            .padding(16.dp)
                            .testTag("history_session_item"),
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
                        modifier = Modifier.testTag("correct_record_weight"),
                    )
                    OutlinedTextField(
                        value = reps,
                        onValueChange = { reps = it },
                        label = { Text(stringResource(R.string.active_session_reps)) },
                        modifier = Modifier.testTag("correct_record_reps"),
                    )
                    OutlinedTextField(
                        value = reason,
                        onValueChange = { reason = it },
                        label = { Text(stringResource(R.string.correct_record_reason)) },
                        modifier = Modifier.testTag("correct_record_reason"),
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = { onEvent(HistoryEvent.ConfirmCorrection(weight, reps, reason)) },
                    modifier = Modifier.testTag("correct_record_confirm"),
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

@Composable
private fun SessionDetailContent(
    detail: HistorySessionDetailUiModel?,
    isLoading: Boolean,
    error: com.openfitness.application.error.AppError?,
    onCorrect: (com.openfitness.domain.valueobject.SetLogId) -> Unit,
    modifier: Modifier = Modifier,
) {
    val resources = LocalContext.current.resources

    when {
        isLoading -> LoadingContent(modifier)
        error != null -> ErrorContent(
            message = error.toMessage(resources),
            onRetry = null,
            modifier = modifier,
        )
        detail == null -> LoadingContent(modifier)
        else -> LazyColumn(
            modifier = modifier
                .fillMaxSize()
                .testTag("history_session_detail"),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(detail.setLogs, key = { it.id.toString() }) { setLog ->
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = stringResource(
                                R.string.active_session_set_line,
                                setLog.setNumber,
                                setLog.weightKg ?: 0.0,
                                setLog.reps ?: 0,
                            ),
                            style = MaterialTheme.typography.bodyLarge,
                            modifier = Modifier.testTag("history_set_item"),
                        )
                        TextButton(
                            onClick = { onCorrect(setLog.id) },
                            modifier = Modifier.testTag("correct_set_button"),
                        ) {
                            Text(stringResource(R.string.history_correct_action))
                        }
                    }
                    setLog.corrections.forEach { correction ->
                        Text(
                            text = stringResource(
                                R.string.history_correction_line,
                                correction.weightKg ?: 0.0,
                                correction.reps ?: 0,
                            ),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier
                                .padding(start = 8.dp, top = 4.dp)
                                .testTag("history_correction_item"),
                        )
                        correction.reason?.let { correctionReason ->
                            Text(
                                text = correctionReason,
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.padding(start = 8.dp),
                            )
                        }
                    }
                }
            }
        }
    }
}
