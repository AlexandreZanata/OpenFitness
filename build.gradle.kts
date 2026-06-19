plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.jvm) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.hilt) apply false
    alias(libs.plugins.ksp) apply false
}

tasks.register<Exec>("scanSecrets") {
    group = "verification"
    description = "Scans tracked files for accidental secrets"
    commandLine("bash", "scripts/scan-secrets.sh")
    isIgnoreExitValue = false
}

tasks.register<Exec>("validateRepoBaseline") {
    group = "verification"
    description = "Validates gitignore, cursor rules, and commit conventions (Gate 0.1)"
    commandLine("bash", "scripts/validate-repo-baseline.sh")
    isIgnoreExitValue = false
}

tasks.register("securityCheck") {
    group = "verification"
    description = "Runs security verification tasks"
    dependsOn(
        "scanSecrets",
        ":domain:test",
    )
}

tasks.register<Exec>("validateReleaseBuild") {
    group = "verification"
    description = "Builds and validates signed release APK/AAB"
    commandLine("bash", "scripts/validate-release-build.sh")
    isIgnoreExitValue = false
}
