# Business Rules

Explicit, named, testable business rules. Each rule is documented in business language **before** code and covered by domain unit tests.

## Index

| Code | Name | Entity |
|------|------|--------|
| BR-001 | [Exercise name uniqueness](BR-001-exercise-name-uniqueness.md) | Exercise |
| BR-002 | [Positive set values](BR-002-positive-set-values.md) | SetLog |
| BR-003 | [Session must have exercises](BR-003-session-must-have-exercises.md) | WorkoutTemplate, WorkoutSession |
| BR-004 | [Completed set requires metrics](BR-004-completed-set-requires-metrics.md) | SetLog |
| BR-005 | [PR only on session completion](BR-005-pr-only-on-session-completion.md) | PersonalRecord |
| BR-006 | [Immutable workout history](BR-006-immutable-workout-history.md) | WorkoutSession, SetLog, PersonalRecord |
| BR-007 | [Bundled exercise immutability](BR-007-bundled-exercise-immutability.md) | Exercise |
| BR-008 | [Set editable in progress only](BR-008-set-editable-in-progress-only.md) | WorkoutSession, SetLog |
| BR-009 | [Correction via new record](BR-009-correction-via-new-record.md) | RecordCorrection |

## Standard Format

Every rule document contains:

1. **Identifier** — `BR-NNN`
2. **GIVEN / WHEN / THEN / AND**
3. **Implementation location** — domain class
4. **Applied use cases**
5. **Test cases** — TDD specs

## Policy

- Rules live **only** in `:domain` — never duplicated in ViewModels or repositories
- Application layer orchestrates; it does not re-implement rules
- One failing assertion per test
