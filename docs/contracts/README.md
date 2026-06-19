# Contracts

Technical interfaces between layers. Ports live in Domain; UI and error contracts live in Application and App.

## Index

| Contract | Document |
|----------|----------|
| Repository ports | [repository-ports.md](repository-ports.md) |
| Use case signatures | [use-case-contracts.md](use-case-contracts.md) |
| UI state pattern | [ui-state-contracts.md](ui-state-contracts.md) |
| Error model | [error-model.md](error-model.md) |
| Database schema | [database-schema.md](database-schema.md) |

## Principles

- Interfaces defined in `:domain` — implementations in `:data`
- Use cases return `Result<T, AppError>` or throw mapped domain exceptions
- UI never sees domain models directly — uses `UiModel` mappers in `:app`
- All contracts versioned with the app — no silent breaking changes
