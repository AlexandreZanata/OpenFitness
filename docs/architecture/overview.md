# Architecture Overview

OpenFitness is structured as **Clean Architecture** with four layers and four Gradle modules. Inner layers never depend on outer layers.

## Layer Diagram

```
┌─────────────────────────────────────────────────────────┐
│  INTERFACES — :app                                      │
│  Compose screens, ViewModels, navigation, theme, i18n │
│  Responsibility: render state, capture user events    │
│  MUST NOT: SQL, HTTP, business rules, parsing         │
└──────────────────────────┬──────────────────────────────┘
                           │ calls
┌──────────────────────────▼──────────────────────────────┐
│  APPLICATION — :application                             │
│  Use cases, flow validation, error mapping              │
│  Responsibility: execute product use cases              │
│  MUST NOT: Android SDK, ORM, UI framework              │
└──────────────────────────┬──────────────────────────────┘
                           │ uses
┌──────────────────────────▼──────────────────────────────┐
│  DOMAIN — :domain                                       │
│  Entities, Value Objects, rules, events, ports          │
│  Responsibility: all business truth                     │
│  MUST NOT: any framework or I/O                         │
└──────────────────────────▲──────────────────────────────┘
                           │ implements
┌──────────────────────────┴──────────────────────────────┐
│  INFRASTRUCTURE — :data                                 │
│  Room, DataStore, parsers, WorkManager, mappers         │
│  Responsibility: persistence and external I/O           │
│  MUST NOT: UI logic, business rules                     │
└─────────────────────────────────────────────────────────┘
```

## Module Map

| Gradle module | Layer | Depends on |
|---------------|-------|------------|
| `:domain` | Domain | Nothing (pure Kotlin) |
| `:application` | Application | `:domain` |
| `:data` | Infrastructure | `:domain`, Android SDK |
| `:app` | Interfaces | `:application`, `:data` (DI wiring only) |

## Golden Rules

1. **Domain** imports zero external frameworks.
2. **Application** depends only on **Domain**.
3. **Infrastructure** implements ports defined in **Domain** — never the reverse.
4. **UI** calls **use cases** — never repositories, DAOs, or HTTP clients directly.
5. Repository **interfaces** live in Domain; **implementations** live in `:data`.
6. **No business logic** in Composables, ViewModels, DAOs, or Workers.

## Feature Organization

UI code is organized **by feature**, not by technical type:

```
app/src/main/kotlin/com/openfitness/app/
├── navigation/
├── theme/
├── di/
├── feature/
│   ├── exerciselibrary/
│   ├── workouttemplate/
│   ├── activesession/
│   ├── history/
│   └── personalrecords/
└── common/
    ├── error/
    └── mapper/
```

## Related Documents

- [Layers and Dependencies](layers-and-dependencies.md)
- [Modules](modules.md)
- [Package Structure](package-structure.md)
- [Data Flow](data-flow.md)
- [Contracts](../contracts/README.md)
