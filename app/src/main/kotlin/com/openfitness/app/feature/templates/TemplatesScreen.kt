package com.openfitness.app.feature.templates

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TemplatesScreen(
    state: TemplatesUiState,
    onEvent: (TemplatesEvent) -> Unit,
) {
    val resources = LocalContext.current.resources
    val editingTemplate = state.editingTemplateId?.let { id ->
        state.templates.firstOrNull { it.id == id }
    }
    val firstExerciseId = state.availableExercises.firstOrNull()?.first

    Scaffold(
        topBar = { TopAppBar(title = { Text(stringResource(R.string.templates_title)) }) },
        floatingActionButton = {
            FloatingActionButton(onClick = { onEvent(TemplatesEvent.ShowCreateDialog) }) {
                Icon(Icons.Default.Add, contentDescription = stringResource(R.string.templates_add))
            }
        },
    ) { padding ->
        when {
            state.isLoading -> LoadingContent(Modifier.padding(padding))
            state.error != null -> ErrorContent(
                error = state.error,
                onRetry = { onEvent(TemplatesEvent.Retry) },
                onDismiss = { onEvent(TemplatesEvent.Retry) },
                modifier = Modifier.padding(padding),
            )
            state.isEmpty && firstExerciseId != null -> Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(16.dp),
            ) {
                EmptyContent(
                    title = stringResource(R.string.templates_empty),
                    ctaLabel = null,
                    onCtaClick = null,
                )
                Button(
                    onClick = {
                        onEvent(
                            TemplatesEvent.StartWorkout(
                                exerciseIds = listOf(firstExerciseId),
                                templateId = null,
                            ),
                        )
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("start_quick_workout"),
                ) {
                    Text(stringResource(R.string.templates_quick_start))
                }
            }
            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                if (firstExerciseId != null) {
                    item {
                        Button(
                            onClick = {
                                onEvent(
                                    TemplatesEvent.StartWorkout(
                                        exerciseIds = listOf(firstExerciseId),
                                        templateId = null,
                                    ),
                                )
                            },
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp)
                                .testTag("start_quick_workout"),
                        ) {
                            Text(stringResource(R.string.templates_quick_start))
                        }
                    }
                }
                items(state.templates, key = { it.id.toString() }) { template ->
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onEvent(TemplatesEvent.ShowEditDialog(template.id)) }
                            .padding(horizontal = 16.dp, vertical = 8.dp),
                    ) {
                        Text(text = template.name, style = MaterialTheme.typography.titleMedium)
                        Text(
                            text = stringResource(R.string.templates_exercise_count, template.exerciseCount),
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
                }
            }
        }
    }

    if (state.showCreateDialog && firstExerciseId != null) {
        TemplateNameDialog(
            title = stringResource(R.string.templates_add),
            onDismiss = { onEvent(TemplatesEvent.DismissCreateDialog) },
            onConfirm = { name -> onEvent(TemplatesEvent.CreateTemplate(name, firstExerciseId)) },
        )
    }

    if (state.showEditDialog && editingTemplate != null) {
        TemplateNameDialog(
            title = stringResource(R.string.edit_template_title),
            initialName = editingTemplate.name,
            onDismiss = { onEvent(TemplatesEvent.DismissEditDialog) },
            onConfirm = { name -> onEvent(TemplatesEvent.UpdateTemplate(editingTemplate.id, name)) },
        )
    }
}

@Composable
private fun TemplateNameDialog(
    title: String,
    initialName: String = "",
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    var name by remember(initialName) { mutableStateOf(initialName) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text(stringResource(R.string.template_name_label)) },
            )
        },
        confirmButton = {
            TextButton(onClick = { onConfirm(name) }) {
                Text(stringResource(R.string.action_save))
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.action_cancel))
            }
        },
    )
}
