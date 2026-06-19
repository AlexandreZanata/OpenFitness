#!/usr/bin/env bash
# Builds and validates signed release APK.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/signing.properties" ]]; then
    echo "ERROR: signing.properties not found."
    echo "Run: cp signing.properties.example signing.properties"
    echo "Or:  ./scripts/create-release-keystore.sh"
    exit 1
fi

./gradlew :app:assembleRelease :app:verifyReleaseApkSize --no-daemon

APK_DIR="$ROOT/app/build/outputs/apk/release"
APK="$(find "$APK_DIR" -maxdepth 1 -name '*.apk' -type f | head -1)"

if [[ -z "$APK" ]]; then
    echo "ERROR: release APK not found in $APK_DIR"
    exit 1
fi

echo "Release build OK: $APK"
