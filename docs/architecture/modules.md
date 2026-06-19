# Gradle Modules

## `:domain`

| Property | Value |
|----------|-------|
| **Plugin** | `java-library` / Kotlin JVM |
| **Dependencies** | Kotlin stdlib only |
| **DI** | None — zero annotations |
| **Tests** | JUnit 5, pure unit tests |

**Contains:**

- `model/` — entities and aggregates
- `valueobject/` — immutable validated types
- `rule/` — business rule classes
- `state/` — state machines
- `event/` — domain events
- `repository/` — port interfaces
- `exception/` — domain exceptions

**Coverage target:** ≥ 90% (JaCoCo)

---

## `:application`

| Property | Value |
|----------|-------|
| **Plugin** | `java-library` / Kotlin JVM |
| **Dependencies** | `:domain`, Coroutines |
| **DI** | None — plain classes injectable by Hilt in `:app` / `:data` |
| **Tests** | JUnit 5, MockK, Turbine |

**Contains:**

- `usecase/` — one class per use case
- `error/` — `AppError` sealed hierarchy
- `dispatcher/` — coroutine dispatcher abstraction (port)

---

## `:data`

| Property | Value |
|----------|-------|
| **Plugin** | `com.android.library` |
| **Dependencies** | `:domain`, Room, DataStore, OkHttp, WorkManager, Hilt |
| **Tests** | JUnit 5, MockK, Room in-memory, MockWebServer |

**Contains:**

- `local/` — Room database, DAOs, entities
- `preferences/` — DataStore
- `mapper/` — persistence ↔ domain
- `repository/` — port implementations
- `worker/` — WorkManager workers
- `parser/` — bundled exercise catalog JSON parser
- `di/` — Hilt modules for data layer

---

## `:app`

| Property | Value |
|----------|-------|
| **Plugin** | `com.android.application` |
| **applicationId** | `com.openfitness.app` |
| **Dependencies** | `:application`, `:data`, Compose BOM, Hilt, Navigation |
| **Tests** | Compose UI Test, instrumented tests |

**Contains:**

- `navigation/` — NavHost, routes
- `theme/` — Material 3 tokens, light/dark
- `feature/` — screens per product feature
- `viewmodel/` — or colocated inside `feature/`
- `mapper/` — `AppError` → localized string
- `di/` — Hilt app module, use case bindings

---

## Module Dependency Graph

```
:app
 ├── :application
 │    └── :domain
 └── :data
      └── :domain
```

`:application` and `:data` are **siblings** — they never depend on each other.
