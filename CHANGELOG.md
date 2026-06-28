# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- NutriOffline Phase 4: fine-tuning dataset gate (`scripts/validate-nutri-dataset.sh`)
- NutriOffline Phase 3: RAG index gate (`scripts/validate-nutri-rag.sh`)
- NutriOffline Phase 2: normalization gate (`scripts/validate-nutri-normalization.sh`)
- NutriOffline Phase 1: data acquisition gate (`scripts/validate-nutri-data-acquisition.sh`)
- NutriOffline Phase 0: hardware validation script (`scripts/validate-nutri-hardware.sh`) and local ML docs (`docs/nutri-offline-local.md`)
- Project scaffold: Gradle multi-module (`:domain`, `:application`, `:data`, `:app`)
- Technical documentation in `docs/` (architecture, entities, business rules, use cases, contracts)
- Cursor agent rules in `.cursor/rules/`
- Local implementation tracker in `.local/` (gitignored)
- CI workflow (GitHub Actions)
- MIT License

## [1.0.0] - TBD

### Planned

- Exercise library (bundled + custom)
- Workout templates and active sessions
- Set logging with personal records
- Immutable workout history
- i18n: English (default) and Brazilian Portuguese

[Unreleased]: https://github.com/AlexandreZanata/OpenFitness/compare/main...HEAD
[1.0.0]: https://github.com/AlexandreZanata/OpenFitness/releases/tag/v1.0.0
