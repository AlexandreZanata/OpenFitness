# Value Objects

Immutable, self-validating types. Invalid values **never exist** as objects — construction fails with a domain exception.

## Index

| Value Object | Document |
|--------------|----------|
| ExerciseId | [exercise-id.md](exercise-id.md) |
| SessionId | [session-id.md](session-id.md) |
| Weight | [weight.md](weight.md) |
| RepCount | [rep-count.md](rep-count.md) |
| Duration | [duration.md](duration.md) |
| MuscleGroup | [muscle-group.md](muscle-group.md) |

## Shared Properties

- Immutable (`data class` with no mutable fields)
- Equality by value
- Validation in `init` or factory companion
- No framework dependencies
- Serializable to primitives at infrastructure boundary only
