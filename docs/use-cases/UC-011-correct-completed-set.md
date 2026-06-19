# UC-011 — Correct Completed Set

| Property | Value |
|----------|-------|
| **Code** | `UC-011` |
| **Actor** | User |
| **Use Case** | `CorrectCompletedSetUseCase` |

## Preconditions

- Session status is `COMPLETED`
- Original set log exists in session history

## Main Flow

1. User opens workout history and selects a completed session.
2. User chooses "Correct entry" on a set log.
3. User enters corrected weight/reps and optional reason.
4. System validates BR-009.
5. System appends `RecordCorrection` — original set log unchanged.
6. UI shows correction chain alongside original entry.

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| Session not COMPLETED | `AppError.ValidationError` — direct edit blocked |
| Set not found | `AppError.NotFound` |
| User attempts in-place edit | Redirect to correction flow only (BR-006) |

## Applied Rules

- BR-006, BR-009

## Events Fired

None (v1) — append-only correction record

## UI States

`success` with correction badge; `error` on validation failure

## i18n Keys

- `correct_record_title`
- `correct_record_reason`
- `error_session_completed`
