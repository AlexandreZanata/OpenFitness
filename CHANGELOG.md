# Changelog

All notable changes to this project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- NutriOffline pipeline moved into repository at `nutri-offline/` (scripts, tests, phase docs)
- NutriOffline user guide at `docs/nutri-offline.md` (replaces `nutri-offline-local.md`)
- NutriOffline Phase 7: offline app integration gate (`scripts/validate-nutri-app.sh`)
- NutriOffline Phase 6: GGUF inference gate (`scripts/validate-nutri-inference.sh`)
- NutriOffline Phase 4: fine-tuning dataset gate (`scripts/validate-nutri-dataset.sh`)
- NutriOffline Phase 3: RAG index gate (`scripts/validate-nutri-rag.sh`)
- NutriOffline Phase 2: normalization gate (`scripts/validate-nutri-normalization.sh`)
- NutriOffline Phase 1: data acquisition gate (`scripts/validate-nutri-data-acquisition.sh`)
- NutriOffline Phase 0: hardware validation script (`scripts/validate-nutri-hardware.sh`)
- Project scaffold: Gradle multi-module (`:domain`, `:application`, `:data`, `:app`)
- Technical documentation in `docs/` (architecture, entities, business rules, use cases, contracts)
- Cursor agent rules in `.cursor/rules/`
- CI workflow (GitHub Actions)
- MIT License

### Changed

- Quality gate scripts now target `nutri-offline/` instead of `.local/nutri-offline/`
- `.local/` retained for gitignored keystores only

## [1.0.0] - TBD

### Planned

- Exercise library (bundled + custom)
- Workout templates and active sessions
- Set logging with personal records
- Immutable workout history
- i18n: English (default) and Brazilian Portuguese

[Unreleased]: https://github.com/AlexandreZanata/OpenFitness/compare/main...HEAD
[1.0.0]: https://github.com/AlexandreZanata/OpenFitness/releases/tag/v1.0.0
