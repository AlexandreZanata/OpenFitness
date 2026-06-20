# Entity — RecordCorrection

| Property | Value |
|----------|-------|
| **Aggregate Root** | Yes (append-only) |
| **Package** | `com.openfitness.domain.model.RecordCorrection` |

## Purpose

Append-only correction record for a set log in a **completed** session (BR-009). The original `SetLog` row is never mutated — corrections form an audit chain alongside history.

## Fields

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String` | Domain-generated UUID |
| `sessionId` | `SessionId` | Must reference a COMPLETED session |
| `originalSetLogId` | `SetLogId` | Set being corrected |
| `correctedWeight` | `Weight?` | New weight (BR-002 if present) |
| `correctedReps` | `RepCount?` | New reps (BR-002 if present) |
| `reason` | `String?` | Optional user note |
| `createdAt` | `Instant` | Append timestamp |

## Invariants

- Created only via `RecordCorrection.create()` factory
- At least one of `correctedWeight` or `correctedReps` should be meaningful (validated at use case boundary)
- `reason` trimmed; empty strings stored as `null`

## Applied Rules

- BR-006 — original set log and session history remain immutable
- BR-009 — correction via new record only

## Related

- [UC-011 — Correct Completed Set](../use-cases/UC-011-correct-completed-set.md)
- [BR-009](../business-rules/BR-009-correction-via-new-record.md)
