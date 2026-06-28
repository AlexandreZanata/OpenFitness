# OpenFitness — Project Documentation

Technical and domain documentation for **OpenFitness**, an Android-native, offline-first personal workout tracker.

All documentation is written in **English** and is the source of truth for humans and coding agents. When code conflicts with these documents, **these documents prevail**.

## Quick Links

| Document | Description |
|----------|-------------|
| [Tech Stack](tech-stack.md) | Exact versions, modules, and excluded technologies |
| [Architecture Overview](architecture/overview.md) | Clean Architecture layers and module map |
| [Glossary](glossary.md) | Ubiquitous language — domain terms |

## Documentation Map

```
docs/
├── README.md                    ← you are here
├── tech-stack.md
├── glossary.md
├── architecture/
│   ├── overview.md
│   ├── layers-and-dependencies.md
│   ├── modules.md
│   ├── package-structure.md
│   └── data-flow.md
├── entities/                    ← aggregates and entity specs
├── value-objects/               ← immutable validated types
├── business-rules/              ← BR-xxx rules (GIVEN/WHEN/THEN)
├── state-machines/              ← lifecycle transitions
├── domain-events/               ← immutable past-tense facts
├── use-cases/                   ← UC-xxx flows
├── contracts/                   ← ports, UI state, errors, DB schema
└── nutri-offline.md             ← NutriOffline ML pipeline (nutri-offline/)
```

## Product Scope (v1)

OpenFitness v1 is **100% on-device**. No backend, no account system, no cloud sync.

| In scope | Out of scope (v1) |
|----------|-------------------|
| Exercise library (bundled + user-created) | Social features |
| Workout templates | Cloud backup |
| Active workout sessions with set logging | Nutrition tracking |
| Workout history (immutable) | Wearable integration |
| Personal records (PRs) | Analytics / Firebase |
| Rest timer during sessions | Multi-user / RBAC |

## Reading Order for New Contributors

1. [Glossary](glossary.md) — learn domain language
2. [Architecture Overview](architecture/overview.md) — understand layers
3. [Entities](entities/README.md) — core aggregates
4. [Business Rules](business-rules/README.md) — rules before code
5. [Use Cases](use-cases/README.md) — product flows
6. [Contracts](contracts/README.md) — technical interfaces
7. [NutriOffline ML pipeline](nutri-offline.md) — QLoRA + RAG in `nutri-offline/`
8. [Implementation Order](implementation-order.md) — build sequence

## Contract Statement

> OpenFitness follows Clean Architecture with a pure Domain at the center, use cases in the Application layer, isolated Infrastructure for I/O, and UI without business logic. Every feature starts from a documented use case, with domain rules tested (TDD) before any UI code. User-visible strings use i18n; errors are structured; workout history is immutable; and security/privacy are requirements from day one.
