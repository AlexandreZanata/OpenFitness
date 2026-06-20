package com.openfitness.app.common.component

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.openfitness.app.R
import com.openfitness.application.error.AppError
import com.openfitness.app.common.error.RecoveryAction
import com.openfitness.app.common.error.toMessage
import com.openfitness.app.common.error.toRecoveryAction

@Composable
fun LoadingContent(modifier: Modifier = Modifier) {
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator()
    }
}

@Composable
fun EmptyContent(
    title: String,
    ctaLabel: String?,
    onCtaClick: (() -> Unit)?,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = title, style = MaterialTheme.typography.titleMedium)
        if (ctaLabel != null && onCtaClick != null) {
            Button(onClick = onCtaClick, modifier = Modifier.padding(top = 16.dp)) {
                Text(text = ctaLabel)
            }
        }
    }
}

@Composable
fun ErrorContent(
    error: AppError,
    onRetry: (() -> Unit)? = null,
    onDismiss: (() -> Unit)? = null,
    onNavigateBack: (() -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    val resources = androidx.compose.ui.platform.LocalContext.current.resources
    val message = error.toMessage(resources)
    val recovery = error.toRecoveryAction()

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(text = message, style = MaterialTheme.typography.bodyLarge)
        when (recovery) {
            RecoveryAction.Retry -> onRetry?.let { handler ->
                Button(onClick = handler, modifier = Modifier.padding(top = 16.dp)) {
                    Text(text = stringResource(R.string.action_retry))
                }
            }
            RecoveryAction.Dismiss -> onDismiss?.let { handler ->
                Button(onClick = handler, modifier = Modifier.padding(top = 16.dp)) {
                    Text(text = stringResource(R.string.action_dismiss))
                }
            }
            RecoveryAction.NavigateBack -> onNavigateBack?.let { handler ->
                Button(onClick = handler, modifier = Modifier.padding(top = 16.dp)) {
                    Text(text = stringResource(R.string.action_back))
                }
            }
            null -> Unit
        }
    }
}
