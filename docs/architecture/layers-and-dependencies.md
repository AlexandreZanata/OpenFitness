# Layers and Dependencies

Dependency direction is **strictly inward**. Violations are architectural defects and must be fixed, not tolerated.

## Dependency Matrix

| From ↓ / To → | Domain | Application | Infrastructure | UI |
|---------------|--------|-------------|----------------|-----|
| **Domain** | — | ❌ | ❌ | ❌ |
| **Application** | ✅ | — | ❌ | ❌ |
| **Infrastructure** | ✅ (ports only) | ❌ | internal | ❌ |
| **UI** | ❌ | ✅ | ✅ (DI modules only) | internal |

## Per-Layer Responsibilities

### Domain (`:domain`)

| Owns | Does not own |
|------|--------------|
| Entities and aggregates | SQL queries |
| Value Objects and invariants | HTTP calls |
| Business rules (`BR-xxx`) | Compose UI |
| State machines | ViewModels |
| Domain events | DTOs from Room |
| Repository port interfaces | Android Context |

### Application (`:application`)

| Owns | Does not own |
|------|--------------|
| Use cases (`UC-xxx`) | Direct database access |
| Authorization checks (future) | UI state mapping |
| Orchestration of domain + ports | Framework annotations in domain |
| Mapping domain exceptions → `AppError` | Business rule implementation |

### Infrastructure (`:data`)

| Owns | Does not own |
|------|--------------|
| Room entities, DAOs, migrations | Business decisions |
| Repository implementations | Use case logic |
| DTO ↔ domain mappers | Compose screens |
| WorkManager workers | Domain event semantics |
| Asset/bundled catalog parser | |

### UI (`:app`)

| Owns | Does not own |
|------|--------------|
| Composables and previews | Business rules |
| ViewModels (UiState, UiEvent) | Repository calls |
| Navigation graph | Set validation logic |
| Theme and design tokens | Direct DAO usage |
| i18n string resolution | |

## DI Exception

`:app` may depend on `:data` **only** for Hilt module wiring (`@Module` classes that bind implementations to ports). ViewModels and Composables must never inject concrete repository or DAO classes.

```kotlin
// ✅ ViewModel
class ActiveSessionViewModel @Inject constructor(
    private val logSet: LogSetUseCase,
    private val completeSession: CompleteWorkoutSessionUseCase,
) : ViewModel()

// ❌ ViewModel
class ActiveSessionViewModel @Inject constructor(
    private val setLogDao: SetLogDao,
) : ViewModel()
```

## Enforcement

- `:domain` build.gradle must have **no** Android plugin and **no** Hilt/Room dependencies.
- ArchUnit or module dependency lint rules should verify the matrix at CI time (planned).
