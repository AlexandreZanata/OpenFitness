# Local Build

Compile and run OpenFitness on a device or emulator.

## Prerequisites

| Requirement | Version |
|-------------|---------|
| JDK | **17** |
| Android SDK | **compileSdk 35**, **minSdk 26** |
| Gradle | Wrapper included (`./gradlew`) |

## Setup

1. Clone the repository.
2. Create `local.properties` in the project root (gitignored):

```properties
sdk.dir=/path/to/Android/Sdk
```

Android Studio creates this automatically when opening the project.

3. Sync Gradle and verify baseline:

```bash
./gradlew validateRepoBaseline
```

## Build commands

```bash
# All JVM unit tests
./gradlew test

# Debug APK
./gradlew :app:assembleDebug

# Install on connected device/emulator
./gradlew :app:installDebug
```

Debug APK output: `app/build/outputs/apk/debug/app-debug.apk`

## Module tests

```bash
./gradlew :domain:test
./gradlew :domain:jacocoTestReport
./gradlew :application:test
./gradlew :data:testDebugUnitTest
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `SDK location not found` | Create `local.properties` with `sdk.dir` |
| JDK version mismatch | Use JDK 17 (`jvmToolchain(17)` in Gradle) |
| Hilt / KSP errors | `./gradlew clean` then rebuild |

See [docs/tech-stack.md](tech-stack.md) for exact dependency versions.
