# Domain Event — PersonalRecordAchieved

| Property | Value |
|----------|-------|
| **Name** | `PersonalRecordAchieved` |
| **Aggregate** | `PersonalRecord` |
| **Raised by** | `PersonalRecord.tryUpdate()` during session completion |

## Payload

| Field | Type |
|-------|------|
| `exerciseId` | `ExerciseId` |
| `metric` | `PersonalRecordMetric` |
| `previousValue` | `Double?` |
| `newValue` | `Double` |
| `sessionId` | `SessionId` |
| `setLogId` | `SetLogId` |
| `achievedAt` | `Instant` |

## When

```
GIVEN a completing session
WHEN  a set strictly exceeds the current PR for an exercise/metric
THEN  PersonalRecordAchieved is raised
AND   the PR record is updated (previous preserved in history)
```

## Use Cases

- [UC-005](../use-cases/UC-005-complete-workout-session.md)
- [UC-007](../use-cases/UC-007-view-personal-records.md)
