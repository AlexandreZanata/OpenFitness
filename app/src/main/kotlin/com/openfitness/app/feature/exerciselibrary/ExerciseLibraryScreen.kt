package com.openfitness.app.feature.exerciselibrary

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
import com.openfitness.app.common.mapper.labelRes
import com.openfitness.domain.valueobject.EquipmentType
import com.openfitness.domain.valueobject.MuscleGroup

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExerciseLibraryScreen(
    state: ExerciseLibraryUiState,
    onEvent: (ExerciseLibraryEvent) -> Unit,
) {
    val resources = LocalContext.current.resources
    val editingExercise = state.editingExerciseId?.let { id ->
        state.exercises.firstOrNull { it.id == id }
    }

    Scaffold(
        topBar = {
            TopAppBar(title = { Text(stringResource(R.string.exercise_library_title)) })
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { onEvent(ExerciseLibraryEvent.ShowAddDialog) },
                modifier = Modifier.testTag("add_exercise_fab"),
            ) {
                Icon(Icons.Default.Add, contentDescription = stringResource(R.string.exercise_library_add))
            }
        },
    ) { padding ->
        when {
            state.isLoading -> LoadingContent(Modifier.padding(padding))
            state.error != null -> ErrorContent(
                error = state.error,
                onRetry = { onEvent(ExerciseLibraryEvent.Retry) },
                onDismiss = { onEvent(ExerciseLibraryEvent.Retry) },
                modifier = Modifier.padding(padding),
            )
            state.isEmpty -> EmptyContent(
                title = stringResource(R.string.exercise_library_empty),
                ctaLabel = stringResource(R.string.exercise_library_add),
                onCtaClick = { onEvent(ExerciseLibraryEvent.ShowAddDialog) },
                modifier = Modifier.padding(padding),
            )
            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .testTag("exercise_list"),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                item {
                    OutlinedTextField(
                        value = state.searchQuery,
                        onValueChange = { onEvent(ExerciseLibraryEvent.SearchChanged(it)) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp)
                            .testTag("exercise_search"),
                        label = { Text(stringResource(R.string.exercise_library_search)) },
                        singleLine = true,
                    )
                }
                items(state.exercises, key = { it.id.toString() }) { exercise ->
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                if (exercise.isCustom) {
                                    onEvent(ExerciseLibraryEvent.ShowEditDialog(exercise.id))
                                }
                            }
                            .padding(horizontal = 16.dp, vertical = 8.dp),
                    ) {
                        Text(text = exercise.name, style = MaterialTheme.typography.titleMedium)
                        Text(
                            text = stringResource(exercise.muscleGroup.labelRes()),
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
                }
            }
        }
    }

    if (state.showAddDialog) {
        ExerciseFormDialog(
            title = stringResource(R.string.exercise_library_add),
            onDismiss = { onEvent(ExerciseLibraryEvent.DismissAddDialog) },
            onConfirm = { name, muscle, equipment ->
                onEvent(ExerciseLibraryEvent.CreateCustom(name, muscle, equipment))
            },
        )
    }

    if (state.showEditDialog && editingExercise != null) {
        ExerciseFormDialog(
            title = stringResource(R.string.edit_exercise_title),
            initialName = editingExercise.name,
            onDismiss = { onEvent(ExerciseLibraryEvent.DismissEditDialog) },
            onConfirm = { name, muscle, equipment ->
                onEvent(ExerciseLibraryEvent.UpdateCustom(editingExercise.id, name, muscle, equipment))
            },
        )
    }
}

@Composable
private fun ExerciseFormDialog(
    title: String,
    initialName: String = "",
    onDismiss: () -> Unit,
    onConfirm: (String, MuscleGroup, EquipmentType) -> Unit,
) {
    var name by remember(initialName) { mutableStateOf(initialName) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text(stringResource(R.string.exercise_name_label)) },
                modifier = Modifier.testTag("exercise_name_input"),
            )
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(name, MuscleGroup.CHEST, EquipmentType.BARBELL) },
                modifier = Modifier.testTag("exercise_form_confirm"),
            ) {
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
