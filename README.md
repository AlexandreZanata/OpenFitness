# OpenFitness

[![CI](https://github.com/AlexandreZanata/OpenFitness/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexandreZanata/OpenFitness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Open-source Android app for offline-first personal workout tracking — no backend required.

**100% open source and free to use** under the [MIT License](LICENSE). See [docs/license.md](docs/license.md) for attribution requirements.

## Features (v1 — planned)

- Exercise library (bundled catalog + custom exercises)
- Workout templates and active session logging
- Personal records (PRs) on session completion
- Immutable workout history
- Rest timer during sessions
- 100% on-device — no account, no cloud

## Stack

| Concern | Technology |
|---------|------------|
| Language | Kotlin **2.0.21** (JVM 17) |
| UI | Jetpack Compose + Material Design 3 |
| Architecture | Clean Architecture — `:domain` / `:application` / `:data` / `:app` |
| Database | Room + SQLite + FTS5 |
| Preferences | DataStore |
| Background | WorkManager |
| DI | Hilt |
| i18n | `en` (default), `pt-BR` |
| Tests | JUnit 5 + MockK + Turbine |

Full specification: **[docs/tech-stack.md](docs/tech-stack.md)**

## Project structure

```
:app/               # Compose UI, ViewModels, theme, navigation
:application/       # Use cases (UC-001…UC-007)
:domain/            # Entities, value objects, rules, events, ports
:data/              # Room, parser, WorkManager, repositories
docs/               # Architecture, use cases, glossary, contracts
.cursor/rules/      # Agent engineering contract
.local/             # Local implementation phases (gitignored)
scripts/            # Repo validation and release helpers
```

Package root: `com.openfitness`

See **[docs/architecture/overview.md](docs/architecture/overview.md)** for layers, modules, and data flow.

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/glossary.md](docs/glossary.md) | Domain language |
| [docs/use-cases/](docs/use-cases/) | UC-001 … UC-007 |
| [docs/business-rules/](docs/business-rules/) | BR-001 … BR-007 |
| [docs/contracts/](docs/contracts/) | Ports, UI state, DB schema |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributor guide |
| [docs/commit-conventions.md](docs/commit-conventions.md) | Git commit standards |
| [docs/local-build.md](docs/local-build.md) | Local compile and install |
| [docs/release-build.md](docs/release-build.md) | Signed release build |

## Development

Before implementing a feature:

1. Read the use case in `docs/use-cases/` (undocumented flows must not be implemented)
2. Check business rules in `docs/business-rules/`
3. Write domain tests first (TDD, GIVEN/WHEN/THEN)
4. Follow [commit conventions](docs/commit-conventions.md)

### Quick start

```bash
./gradlew validateRepoBaseline   # Gate 0.1 — repo + .cursor rules
./gradlew test                     # unit tests
./gradlew :app:assembleDebug       # debug APK
./gradlew :app:installDebug        # install on device/emulator
```

See **[docs/local-build.md](docs/local-build.md)** for prerequisites and troubleshooting.

## License

This project is released under the **[MIT License](LICENSE)**. Full details: **[docs/license.md](docs/license.md)**.
