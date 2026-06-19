# State Machines

Explicit lifecycle documentation for entities with finite states.

## Index

| Machine | Entity | Document |
|---------|--------|----------|
| Workout Session Lifecycle | `WorkoutSession` | [workout-session-lifecycle.md](workout-session-lifecycle.md) |

## Policy

- State machines live in `:domain`
- Invalid transitions throw `InvalidStateTransitionException`
- Terminal states allow no further transitions
- UI observes status — never sets it directly
