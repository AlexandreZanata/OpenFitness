# Entity — WorkoutTemplate

| Property | Value |
|----------|-------|
| **Aggregate Root** | Yes |
| **Identity** | `TemplateId` (UUID) |
| **Module** | `:domain` → `com.openfitness.domain.model.WorkoutTemplate` |

## Definition

A **WorkoutTemplate** is a reusable workout plan. It defines which exercises to perform and target set counts. It does not store actual performed sets.

## Attributes

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `TemplateId` | yes | Domain-generated UUID |
| `name` | `String` | yes | 2–60 chars |
| `exercises` | `List<TemplateExercise>` | yes | Ordered, min 1 (BR-003) |
| `createdAt` | `Instant` | yes | |
| `updatedAt` | `Instant` | yes | |

### TemplateExercise (child value)

| Field | Type | Required |
|-------|------|----------|
| `exerciseId` | `ExerciseId` | yes |
| `order` | `Int` | yes, 0-based |
| `targetSets` | `Int` | yes, ≥ 1 |
| `targetReps` | `RepCount?` | optional |
| `targetWeight` | `Weight?` | optional |

## Invariants

1. Template name must be non-blank.
2. Must contain at least one exercise (BR-003).
3. Exercise order values are unique within the template.
4. No duplicate `exerciseId` in the same template.
5. `targetSets` ≥ 1 for each entry.

## Behavior

```kotlin
fun addExercise(exerciseId: ExerciseId, targetSets: Int, ...): WorkoutTemplate
fun removeExercise(exerciseId: ExerciseId): WorkoutTemplate
fun reorder(exerciseId: ExerciseId, newOrder: Int): WorkoutTemplate
```

## Relationships

| Related entity | Cardinality | Description |
|----------------|-------------|-------------|
| Exercise | many-to-many | Referenced by `exerciseId` |
| WorkoutSession | one-to-many | Session may be started from template (`UC-003`) |

## Applied Business Rules

| Code | Rule |
|------|------|
| BR-003 | [Session must have exercises](../business-rules/BR-003-session-must-have-exercises.md) |

## Domain Events

None (v1). Template changes are not audited as domain events.

## Use Cases

- [UC-002 Create Workout Template](../use-cases/UC-002-create-workout-template.md)

## Tests Required

- Template with zero exercises fails validation
- Duplicate exercise in template fails
- Reorder updates order indices correctly
