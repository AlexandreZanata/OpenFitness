# Access Control — Permission Matrix (v1)

v1 is a **single-user, on-device** app. No authentication or multi-tenant isolation.

## v1 Model

| Role | Description |
|------|-------------|
| `DeviceOwner` | Implicit — whoever uses the device owns all local data |

All actions are available to the device owner. No role checks in v1 application layer.

## Future Consideration (not v1)

When multi-profile or cloud sync is added, define:

| Action | DeviceOwner | Coach | Viewer |
|--------|-------------|-------|--------|
| Start session | ✅ | — | — |
| View history | ✅ | — | — |
| Export data | ✅ | — | — |

Document changes via ADR before implementation.

## Tenant Isolation

Not applicable in v1. Rule from agent core principles is deferred until backend exists.
