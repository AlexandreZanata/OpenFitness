# Value Object — Duration

| Type | `data class` wrapping `seconds: Long` |
|------|---------------------------------------|
| **Module** | `com.openfitness.domain.valueobject.Duration` |

## Invariants

- Seconds must be **≥ 0**
- Used for rest timer configuration and session elapsed time display

## Factory

```kotlin
data class Duration(val seconds: Long) {
    init {
        require(seconds >= 0) { "Duration cannot be negative" }
    }
    companion object {
        fun fromSeconds(s: Long): Duration
        fun fromMinutes(m: Int): Duration = Duration(m * 60L)
    }
}
```

## Usage

- Rest timer default stored in DataStore (UI preference — not a domain entity)
- Session elapsed time computed in ViewModel from `startedAt` / `completedAt`
