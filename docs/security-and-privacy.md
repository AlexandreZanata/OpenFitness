# Security and Privacy

v1 is local-only — no accounts, no network by default. Security focuses on device data protection and future-proofing.

## Requirements

| Requirement | v1 Status |
|-------------|-----------|
| TLS for external communication | N/A (no network v1); required when catalog download added |
| Encrypt sensitive data at rest | Room database not encrypted v1; evaluate SQLCipher if health data expands |
| No PII in production logs | Enforced — no logging framework in v1 |
| Minimize data collected | Local workout data only — no analytics |
| LGPD/GDPR awareness | No personal identifiers stored beyond device-local workouts |
| Backup rules | `android:allowBackup` configured to exclude sensitive prefs |

## Data Stored

| Data | Sensitivity | Location |
|------|-------------|----------|
| Workout history | Low (user-owned) | Room |
| Exercise names | Low | Room |
| Rest timer preference | None | DataStore |

## Access Control (v1)

Single-user, device-bound. No RBAC in v1. Documented for future multi-profile support in [access-control/permission-matrix.md](access-control/permission-matrix.md).

## ProGuard / R8

Release builds obfuscate `:app` and `:data`. Keep rules for Room, Hilt, and domain models used in reflection.

## Anti-Patterns

- Logging set data or exercise history to Logcat in release
- Sending workout data to LLM (see AI integration rules)
- Adding Firebase/analytics without ADR
