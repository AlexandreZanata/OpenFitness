# UC-007 — View Personal Records

| Property | Value |
|----------|-------|
| **Code** | `UC-007` |
| **Actor** | User |
| **Use Case** | `ViewPersonalRecordsUseCase` |

## Preconditions

- None — empty PR list is valid

## Main Flow

1. User opens Personal Records screen.
2. System loads current PR per exercise/metric.
3. System displays exercise name, metric, value, achieved date.
4. User taps an entry.
5. System shows source session and set reference (read-only).

## Alternative Flows

| Condition | Behavior |
|-----------|----------|
| No PRs yet | Empty state with explanation |
| Exercise deleted from library | PR retained — show exercise name snapshot |

## Applied Rules

- BR-006 (history append-only)

## Events Fired

None (read-only).

## UI States

`loading` → `success` | `empty` | `error`
