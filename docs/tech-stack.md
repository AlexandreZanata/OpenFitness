# Tech Stack — OpenFitness

Exact technology choices for this project. Values mirror the reference Android stack; project-specific identifiers are adapted for OpenFitness.

**App version:** `1.0.0`

---

## Platform

| Item | Value |
|------|-------|
| **Platform** | Native Android (no iOS/KMP/Flutter) |
| **Language** | Kotlin **2.0.21** |
| **JVM target** | **17** |
| **minSdk** | **26** (Android 8.0) |
| **targetSdk** | **35** |
| **compileSdk** | **35** |
| **AGP** (Android Gradle Plugin) | **8.7.3** |
| **KSP** | **2.0.21-1.0.28** |
| **applicationId** | `com.openfitness.app` |
| **versionName** | `1.0.0` |

---

## Architecture and Modules

| Module | Type | Role |
|--------|------|------|
| `:domain` | Pure Kotlin JVM | Entities, rules, ports |
| `:application` | Pure Kotlin JVM | Use cases |
| `:data` | Android library | Room, OkHttp, parsers, workers |
| `:app` | Android application | Compose, ViewModels, UI |

**Pattern:** Clean Architecture (4 layers)

See [architecture/modules.md](architecture/modules.md) for responsibilities and dependency rules.

---

## UI

| Technology | Version |
|------------|--------|
| **Jetpack Compose** | BOM **2024.12.01** |
| **Material Design 3** | via Compose BOM |
| **Material Icons Extended** | via Compose BOM |
| **Activity Compose** | **1.9.3** |
| **Lifecycle Runtime Compose** | **2.8.7** |
| **Lifecycle ViewModel Compose** | **2.8.7** |
| **Navigation Compose** | **2.8.5** |

---

## Persistence and Preferences

| Technology | Version |
|------------|--------|
| **Room** | **2.6.1** |
| **SQLite + FTS5** | via Room |
| **DataStore Preferences** | **1.1.1** |

---

## Network, Sync, and Parsing

| Technology | Version | Usage |
|------------|--------|-------|
| **OkHttp** | **4.12.0** | Optional remote exercise catalog download (future) |
| **WorkManager** | **2.10.0** | Background reminders, optional catalog refresh |
| **Bundled JSON parser** | custom (`:data:parser`) | Seed exercise catalog from assets |
| **kxml2** | **2.3.0** | **Tests only** (parser fixtures) |

> v1 primary data path is **local Room + bundled assets**. OkHttp is reserved for optional catalog updates in a later iteration.

---

## Async and DI

| Technology | Version |
|------------|--------|
| **Kotlin Coroutines** | **1.9.0** |
| **Kotlin Flow** | via Coroutines |
| **Hilt** | **2.53.1** |
| **Hilt Navigation Compose** | **1.2.0** |
| **Hilt Work** | **1.2.0** |

---

## Testing

| Technology | Version | Where |
|------------|--------|-------|
| **JUnit 5** | **5.11.4** | All modules |
| **MockK** | **1.13.13** | domain, application, data |
| **Turbine** | **1.2.0** | application |
| **Room Testing** | **2.6.1** | data |
| **Compose UI Test** | via BOM | app |
| **MockWebServer** | **4.12.0** | data (tests) |
| **AndroidX Test Orchestrator** | **1.5.1** | instrumented |
| **JaCoCo** | integrated | `:domain` (target ≥ **90%**) |

---

## i18n

| Item | Value |
|------|-------|
| **Mechanism** | Android string resources |
| **Default locale** | `en` (`values/`) |
| **Additional locale** | `pt-BR` (`values-pt-rBR/`) |

See [i18n.md](i18n.md).

---

## Build and Release

| Item | Value |
|------|-------|
| **ProGuard/R8** | enabled in release |
| **Shrink resources** | enabled in release |
| **Release APK size limit** | 15 MB (`verifyReleaseApkSize` task) |

---

## Explicitly Excluded

| Excluded | Reason |
|----------|--------|
| Backend / REST API | 100% on-device (v1) |
| Retrofit | OkHttp sufficient when network is needed |
| Firebase / analytics | v1 without tracking |
| Apache POI in production | Memory risk on Android |
| RxJava | Coroutines + Flow |
| KMP / Flutter | Android-only |
| Plain Dagger (without Hilt) | Hilt reduces boilerplate |
| Jsoup / XLSX scraping | Not applicable to fitness domain |

---

## One-Line Summary

**Kotlin 2.0.21 + Jetpack Compose (Material 3) + Clean Architecture (4 modules) + Room/SQLite/FTS5 + DataStore + WorkManager + bundled JSON parser + Hilt + Coroutines/Flow + JUnit 5/MockK/Turbine**, Android **minSdk 26 / targetSdk 35**.
