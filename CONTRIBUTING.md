# Contributing to OpenFitness

Thank you for contributing. All **source code, commits, and documentation** are in **English**. User-visible strings are localized via Android string resources (`en` default, `pt-BR`).

## Before you start

Read these documents in order:

| Document | Why |
|----------|-----|
| [docs/README.md](docs/README.md) | Documentation index and v1 scope |
| [docs/architecture/overview.md](docs/architecture/overview.md) | Layer boundaries and module dependencies |
| [docs/tech-stack.md](docs/tech-stack.md) | Accepted libraries and versions |
| [docs/glossary.md](docs/glossary.md) | Domain language |
| [docs/business-rules/](docs/business-rules/) | BR-001 … BR-007 |
| [docs/use-cases/](docs/use-cases/) | UC-001 … UC-007 — **undocumented flows must not be implemented** |
| [docs/commit-conventions.md](docs/commit-conventions.md) | Commit and PR format |

Agent engineering rules live in [`.cursor/rules/`](.cursor/rules/).

NutriOffline ML pipeline: [nutri-offline/README.md](nutri-offline/README.md) and [docs/nutri-offline.md](docs/nutri-offline.md).

Local keystores only: `.local/README.md` (gitignored).

## Development setup

**Requirements:** JDK 17, Android SDK (compileSdk 35, minSdk 26 per `docs/tech-stack.md`).

```bash
git clone git@github.com:AlexandreZanata/OpenFitness.git
cd OpenFitness
./gradlew validateRepoBaseline
./gradlew test
./gradlew :app:assembleDebug
```

See **[docs/local-build.md](docs/local-build.md)** for `local.properties`, SDK setup, and troubleshooting.

**Never commit:** `local.properties`, keystores, `signing.properties`, `.env`, `.local/`, or gitignored paths under `nutri-offline/` (`data/`, `models/`, `venv/`, etc.).

## Architecture rules

| Module | Responsibility |
|--------|----------------|
| `:domain` | Entities, value objects, business rules, ports — **pure Kotlin** |
| `:application` | Use cases — depends on `:domain` only |
| `:data` | Room, DataStore, WorkManager — implements domain ports |
| `:app` | Compose UI and ViewModels — calls use cases, never DAOs |

See [docs/architecture/layers-and-dependencies.md](docs/architecture/layers-and-dependencies.md).

## Test-driven development

1. Write failing unit test in `:domain` (GIVEN / WHEN / THEN).
2. Implement minimum code to pass.
3. Target **90%+** instruction coverage on `:domain` (JaCoCo).

```bash
./gradlew test
./gradlew :domain:test
./gradlew :domain:jacocoTestReport
./gradlew securityCheck
```

## Feature checklist

1. Use case exists in `docs/use-cases/`
2. Domain terms match `docs/glossary.md`
3. Business rules tested in `:domain` first
4. i18n keys for all user-visible strings
5. UI states: loading, empty, error, success
6. One logical change per commit (Conventional Commits)

## Pull requests

```markdown
## Summary
- Bullet points of changes

## Use cases
- UC-00X (if applicable)

## Test plan
- [ ] Domain unit tests
- [ ] Use case tests
- [ ] Manual UI verification
```

CI runs `./gradlew test` on every push and PR to `main`.
