# Commit Conventions

All commit messages must be written in **English**.

Format: [Conventional Commits](https://www.conventionalcommits.org/)

```
<type>(<scope>): <subject>

[optional body]

Refs: UC-005
Refs: BR-011
```

## Types

`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`, `revert`

## Scopes

`domain`, `application`, `data`, `api`, `ui`, `auth`, `db`, `deps`, `ci`

## Rules

- Imperative mood, lowercase subject, max 72 characters, no trailing period
- One commit = one logical change
- Never commit secrets, keystores, `.env`, build artifacts
- Agent commits only when explicitly requested

Full agent workflow: `.cursor/rules/commit-conventions.mdc`
