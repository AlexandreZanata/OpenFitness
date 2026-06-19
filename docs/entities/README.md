# Entities

Domain entities and aggregates for OpenFitness. Each file documents one aggregate or standalone entity with its invariants, relationships, and applied business rules.

## Index

| Entity | Aggregate Root | Document |
|--------|----------------|----------|
| Exercise | Yes | [exercise.md](exercise.md) |
| WorkoutTemplate | Yes | [workout-template.md](workout-template.md) |
| WorkoutSession | Yes | [workout-session.md](workout-session.md) |
| SetLog | No (child of WorkoutSession) | [set-log.md](set-log.md) |
| PersonalRecord | Yes | [personal-record.md](personal-record.md) |

## Aggregate Map

```
Exercise (root)
 └── (standalone — referenced by templates, sessions, PRs)

WorkoutTemplate (root)
 └── TemplateExercise (child — exercise ref + target sets)

WorkoutSession (root)
 └── SessionExercise (child — exercise ref + order)
 └── SetLog (child — performed sets)

PersonalRecord (root)
 └── (standalone — keyed by exercise + metric)
```

## Shared Rules

All entities:

- Use domain-generated UUIDs — never database auto-increment as domain identity
- Validate invariants at construction and on state change
- Raise domain events from within the aggregate — not from use cases directly

## Related

- [Value Objects](../value-objects/README.md)
- [Business Rules](../business-rules/README.md)
- [State Machines](../state-machines/README.md)
- [Domain Events](../domain-events/README.md)
