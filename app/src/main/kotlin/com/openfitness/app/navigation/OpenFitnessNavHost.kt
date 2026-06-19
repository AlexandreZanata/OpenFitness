package com.openfitness.app.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FitnessCenter
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.List
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
    val icon: @Composable () -> Unit,
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
        BottomNavItem(
            route = Routes.EXERCISE_LIBRARY,
            labelRes = R.string.nav_exercises,
            testTag = "nav_exercises",
            icon = { Icon(Icons.Default.List, contentDescription = null) },
        ),
        BottomNavItem(
            route = Routes.TEMPLATES,
            labelRes = R.string.nav_workout,
            testTag = "nav_workout",
            icon = { Icon(Icons.Default.FitnessCenter, contentDescription = null) },
        ),
        BottomNavItem(
            route = Routes.HISTORY,
            labelRes = R.string.nav_history,
            testTag = "nav_history",
            icon = { Icon(Icons.Default.History, contentDescription = null) },
        ),
        BottomNavItem(
            route = Routes.PERSONAL_RECORDS,
            labelRes = R.string.nav_records,
            testTag = "nav_records",
            icon = { Icon(Icons.Default.Star, contentDescription = null) },
        ),
    )

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    bottomItems.forEach { item ->
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
                            icon = item.icon,
                            label = { Text(stringResource(item.labelRes)) },
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
            LaunchedEffect(viewModel) {
                viewModel.navigation.collect { sessionId ->
                    navController.navigate(Routes.activeSession(sessionId.toString())) {
                        launchSingleTop = true
                    }
                }
            }
            TemplatesScreen(state = state, onEvent = viewModel::onEvent)
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
