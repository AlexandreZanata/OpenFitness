package com.openfitness.app.feature.personalrecords

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
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
fun PersonalRecordsScreen(
    state: PersonalRecordsUiState,
    onEvent: (PersonalRecordsEvent) -> Unit,
) {
    val resources = LocalContext.current.resources

    Scaffold(
        topBar = { TopAppBar(title = { Text(stringResource(R.string.personal_records_title)) }) },
    ) { padding ->
        when {
            state.isLoading -> LoadingContent(Modifier.padding(padding))
            state.error != null -> ErrorContent(
                message = state.error.toMessage(resources),
                onRetry = { onEvent(PersonalRecordsEvent.Retry) },
                modifier = Modifier.padding(padding),
            )
            state.isEmpty -> EmptyContent(
                title = stringResource(R.string.personal_records_empty),
                ctaLabel = null,
                onCtaClick = null,
                modifier = Modifier.padding(padding),
            )
            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .testTag("personal_records_list"),
            ) {
                items(state.records, key = { "${it.exerciseId}-${it.metric}" }) { record ->
                    Text(
                        text = stringResource(
                            R.string.personal_record_line,
                            record.exerciseId.toString().take(8),
                            record.metric.name,
                            record.value,
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }
        }
    }
}
