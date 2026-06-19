# Entity — Exercise

| Property | Value |
|----------|-------|
| **Aggregate Root** | Yes |
| **Identity** | `ExerciseId` (UUID) |
| **Module** | `:domain` → `com.openfitness.domain.model.Exercise` |

## Definition

An **Exercise** represents a single trainable movement. Exercises come from the bundled catalog or are created by the user as custom exercises.

## Attributes

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `ExerciseId` | yes | Domain-generated UUID |
| `name` | `String` | yes | Trimmed, 2–80 chars |
| `primaryMuscleGroup` | `MuscleGroup` | yes | See glossary |
| `equipmentType` | `EquipmentType` | yes | See glossary |
| `isCustom` | `Boolean` | yes | `true` for user-created |
| `createdAt` | `Instant` | yes | Immutable after creation |

## Invariants

1. Name must be non-blank after trim.
2. Custom exercise names must be unique case-insensitively within the local library (BR-001).
3. Bundled exercises are read-only — name and muscle group cannot be mutated (BR-007).
4. `id` is immutable.

## Behavior

```kotlin
// Conceptual API
class Exercise private constructor(...) {
    companion object {
        fun createCustom(name: String, muscleGroup: MuscleGroup, equipment: EquipmentType): Exercise
        fun restore(id: ExerciseId, ...): Exercise  // reconstitution from persistence
    }
}
```

## Relationships

| Related entity | Cardinality | Description |
|----------------|-------------|-------------|
| WorkoutTemplate | many-to-many | Via `TemplateExercise` |
| WorkoutSession | many-to-many | Via `SessionExercise` |
| PersonalRecord | one-to-many | One PR per metric per exercise |

## Applied Business Rules

| Code | Rule |
|------|------|
| BR-001 | [Exercise name uniqueness](../business-rules/BR-001-exercise-name-uniqueness.md) |
| BR-007 | [Bundled exercise immutability](../business-rules/BR-007-bundled-exercise-immutability.md) |

## Domain Events

None on creation (v1). Future: `CustomExerciseCreated`.

## Persistence Notes

- Indexed in Room FTS5 for library search (`UC-001`).
- Bundled exercises seeded from assets on first launch.

## Tests Required (TDD)

- Custom exercise with valid attributes is created
- Blank name throws `DomainException`
- Duplicate custom name throws `DuplicateExerciseNameException`
- Bundled exercise cannot be renamed
