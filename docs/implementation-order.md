# Implementation Order

Recommended build sequence. **Do not implement UI before domain tests pass.**

## Phase 1 — Domain Foundation

1. Value Objects: `ExerciseId`, `SessionId`, `SetLogId`, `TemplateId`, `Weight`, `RepCount`, `MuscleGroup`, `Duration`
2. Entities: `Exercise`, `SetLog`, `WorkoutTemplate`, `WorkoutSession`, `PersonalRecord`, `RecordCorrection`
3. Business rules: BR-001 through BR-009
4. State machine: `WorkoutSessionStateMachine`
5. Domain events (including `SetLogUpdated` for UC-008)
6. Repository port interfaces

**Gate:** `:domain` unit tests green, JaCoCo ≥ 90%

## Phase 2 — Critical Infrastructure

1. Room schema + migrations + exercise name search (`LIKE` — see `database-schema.md`)
2. `BundledExerciseCatalogParser` + asset seed file
3. `CatalogSeeder` implementation
4. Domain ↔ entity mappers
5. Repository implementations (including `RecordCorrectionRepository`)

**Gate:** Integration tests for seed + CRUD pass

## Phase 3 — Application Layer

1. `AppError` hierarchy
2. Use cases UC-001 through UC-011
3. Helper use cases: `GetWorkoutSessionUseCase`, `GetRecordCorrectionsUseCase`, `ListWorkoutTemplatesUseCase`, `GetExerciseUseCase`, `SeedCatalogUseCase`, `ObserveRestTimerUseCase`
4. Turbine tests for Flow-based queries

**Gate:** All use case tests pass with mocked ports

## Phase 4 — Complete Infrastructure

1. `TransactionRunner`
2. WorkManager `RestReminderWorker` (optional v1.1)
3. DataStore preferences + `UserPreferencesRepository` port

## Phase 5 — UI

1. Theme / design tokens (Material 3, light + dark)
2. Navigation graph
3. Feature screens in order:
   - Exercise Library (UC-001, UC-010)
   - Workout Templates (UC-002, UC-009)
   - Active Session (UC-003, UC-004, UC-005, UC-008)
   - History (UC-006, UC-011)
   - Personal Records (UC-007)
4. Record editing flows: edit set (in progress), edit template, edit custom exercise, correct completed set
5. `ErrorMessageMapper` + i18n keys (`en`, `pt-BR`)

**Gate:** Compose UI tests for happy path + record editing flows

## Phase 6 — Release Hardening

1. ProGuard rules
2. `verifyReleaseApkSize` (15 MB limit)
3. Accessibility pass (labels, contrast, font scaling)
4. Final JaCoCo report

## Feature Checklist (per use case UC-001 through UC-011)

- [ ] Use case documented
- [ ] Business rules referenced
- [ ] Domain tests written first
- [ ] i18n keys for all visible strings
- [ ] UI states: loading, empty, error, success
- [ ] Offline behavior verified
