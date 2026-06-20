package com.openfitness.app.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.FitnessCenter
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.openfitness.app.R
import com.openfitness.app.feature.activesession.ActiveSessionScreen
import com.openfitness.app.feature.activesession.ActiveSessionViewModel
import com.openfitness.app.feature.exerciselibrary.ExerciseLibraryScreen
import com.openfitness.app.feature.exerciselibrary.ExerciseLibraryViewModel
import com.openfitness.app.feature.history.HistoryScreen
import com.openfitness.app.feature.history.HistoryViewModel
import com.openfitness.app.feature.personalrecords.PersonalRecordsScreen
import com.openfitness.app.feature.personalrecords.PersonalRecordsViewModel
import com.openfitness.app.feature.templates.TemplatesScreen
import com.openfitness.app.feature.templates.TemplatesViewModel

private data class BottomNavItem(
    val route: String,
    val labelRes: Int,
    val testTag: String,
)

@Composable
fun OpenFitnessApp() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route
    val showBottomBar = currentRoute in setOf(
        Routes.EXERCISE_LIBRARY,
        Routes.TEMPLATES,
        Routes.HISTORY,
        Routes.PERSONAL_RECORDS,
    )

    val bottomItems = listOf(
        BottomNavItem(Routes.EXERCISE_LIBRARY, R.string.nav_exercises, "nav_exercises"),
        BottomNavItem(Routes.TEMPLATES, R.string.nav_workout, "nav_workout"),
        BottomNavItem(Routes.HISTORY, R.string.nav_history, "nav_history"),
        BottomNavItem(Routes.PERSONAL_RECORDS, R.string.nav_records, "nav_records"),
    )

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    bottomItems.forEach { item ->
                        val label = stringResource(item.labelRes)
                        NavigationBarItem(
                            selected = currentRoute == item.route,
                            onClick = {
                                navController.navigate(item.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = {
                                when (item.route) {
                                    Routes.EXERCISE_LIBRARY -> Icon(
                                        Icons.AutoMirrored.Filled.List,
                                        contentDescription = label,
                                    )
                                    Routes.TEMPLATES -> Icon(
                                        Icons.Default.FitnessCenter,
                                        contentDescription = label,
                                    )
                                    Routes.HISTORY -> Icon(
                                        Icons.Default.History,
                                        contentDescription = label,
                                    )
                                    else -> Icon(
                                        Icons.Default.Star,
                                        contentDescription = label,
                                    )
                                }
                            },
                            label = { Text(label) },
                            modifier = Modifier.testTag(item.testTag),
                        )
                    }
                }
            }
        },
    ) { padding ->
        OpenFitnessNavHost(
            navController = navController,
            modifier = Modifier.padding(padding),
        )
    }
}

@Composable
private fun OpenFitnessNavHost(
    navController: NavHostController,
    modifier: Modifier = Modifier,
) {
    NavHost(
        navController = navController,
        startDestination = Routes.TEMPLATES,
        modifier = modifier,
    ) {
        composable(Routes.EXERCISE_LIBRARY) {
            val viewModel: ExerciseLibraryViewModel = hiltViewModel()
            val state by viewModel.uiState.collectAsStateWithLifecycle()
            ExerciseLibraryScreen(state = state, onEvent = viewModel::onEvent)
        }
        composable(Routes.TEMPLATES) {
            val viewModel: TemplatesViewModel = hiltViewModel()
            val state by viewModel.uiState.collectAsStateWithLifecycle()
            TemplatesScreen(
                state = state,
                onEvent = viewModel::onEvent,
                onSessionStarted = { sessionId ->
                    navController.navigate(Routes.activeSession(sessionId.toString())) {
                        launchSingleTop = true
                    }
                },
                onNavigationConsumed = viewModel::onNavigationConsumed,
            )
        }
        composable(Routes.HISTORY) {
            val viewModel: HistoryViewModel = hiltViewModel()
            val state by viewModel.uiState.collectAsStateWithLifecycle()
            HistoryScreen(state = state, onEvent = viewModel::onEvent)
        }
        composable(Routes.PERSONAL_RECORDS) {
            val viewModel: PersonalRecordsViewModel = hiltViewModel()
            val state by viewModel.uiState.collectAsStateWithLifecycle()
            PersonalRecordsScreen(state = state, onEvent = viewModel::onEvent)
        }
        composable(
            route = Routes.ACTIVE_SESSION,
            arguments = listOf(navArgument("sessionId") { type = NavType.StringType }),
        ) {
            val viewModel: ActiveSessionViewModel = hiltViewModel()
            val state by viewModel.uiState.collectAsStateWithLifecycle()
            ActiveSessionScreen(state = state, onEvent = viewModel::onEvent)
        }
    }
}
