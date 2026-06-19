# Release Build

Signed release APK/AAB for OpenFitness.

## Prerequisites

- JDK 17, Android SDK 35
- Release keystore (never commit)

## Quick setup

```bash
./scripts/create-release-keystore.sh
cp signing.properties.example signing.properties
# Edit signing.properties if you changed the default password
```

Keystore path (gitignored): `.local/openfitness-release.keystore`

## Environment variables (CI alternative)

| Variable | Maps to |
|----------|---------|
| `OPENFITNESS_KEYSTORE_PATH` | `storeFile` |
| `OPENFITNESS_KEYSTORE_PASSWORD` | `storePassword` |
| `OPENFITNESS_KEY_ALIAS` | `keyAlias` |
| `OPENFITNESS_KEY_PASSWORD` | `keyPassword` |

## Build release

```bash
./gradlew :app:assembleRelease
./gradlew :app:verifyReleaseApkSize   # fails if APK > 15 MB
./gradlew validateReleaseBuild        # script wrapper
```

Release APK: `app/build/outputs/apk/release/app-release.apk`

## ProGuard

Release builds use R8 with rules in `app/proguard-rules.pro`. Verify cold start after minification.

See [docs/tech-stack.md](tech-stack.md) § Build and Release.
