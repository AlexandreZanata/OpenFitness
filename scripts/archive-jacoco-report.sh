#!/usr/bin/env bash
# Archives the domain JaCoCo HTML report to .jacoco/ for release verification.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./gradlew :domain:jacocoTestReport --no-daemon

DEST="$ROOT/.jacoco/domain-$(date +%Y%m%d)"
mkdir -p "$DEST"
cp -r domain/build/reports/jacoco/test/html/* "$DEST/"

echo "JaCoCo report archived to $DEST/index.html"
