# Contract — Database Schema

Room schema for `:data`. Version **1** — migrations required for changes.

## Tables

### `exercises`

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID string |
| `name` | TEXT | Indexed |
| `primary_muscle_group` | TEXT | Enum string |
| `equipment_type` | TEXT | Enum string |
| `is_custom` | INTEGER | Boolean |
| `created_at` | INTEGER | Epoch millis |

**FTS:** `exercises_fts` virtual table (FTS5) synced via Room trigger.

### `workout_templates`

| Column | Type |
|--------|------|
| `id` | TEXT PK |
| `name` | TEXT |
| `created_at` | INTEGER |
| `updated_at` | INTEGER |

### `template_exercises`

| Column | Type |
|--------|------|
| `template_id` | TEXT FK |
| `exercise_id` | TEXT FK |
| `order_index` | INTEGER |
| `target_sets` | INTEGER |
| `target_reps` | INTEGER NULL |
| `target_weight_kg` | REAL NULL |

PK: (`template_id`, `exercise_id`)

### `workout_sessions`

| Column | Type |
|--------|------|
| `id` | TEXT PK |
| `template_id` | TEXT NULL FK |
| `status` | TEXT |
| `started_at` | INTEGER NULL |
| `completed_at` | INTEGER NULL |
| `cancelled_at` | INTEGER NULL |

Index: `status`, `completed_at DESC`

### `session_exercises`

| Column | Type |
|--------|------|
| `session_id` | TEXT FK |
| `exercise_id` | TEXT FK |
| `order_index` | INTEGER |

### `set_logs`

| Column | Type |
|--------|------|
| `id` | TEXT PK |
| `session_id` | TEXT FK |
| `exercise_id` | TEXT FK |
| `set_number` | INTEGER |
| `weight_kg` | REAL NULL |
| `reps` | INTEGER NULL |
| `completed_at` | INTEGER |

Index: (`session_id`, `exercise_id`)

### `personal_records`

| Column | Type |
|--------|------|
| `exercise_id` | TEXT |
| `metric` | TEXT |
| `value` | REAL |
| `achieved_at` | INTEGER |
| `session_id` | TEXT |
| `set_log_id` | TEXT |

PK: (`exercise_id`, `metric`)

### `personal_record_history`

| Column | Type |
|--------|------|
| `id` | TEXT PK |
| `exercise_id` | TEXT |
| `metric` | TEXT |
| `value` | REAL |
| `achieved_at` | INTEGER |
| `session_id` | TEXT |
| `set_log_id` | TEXT |
| `superseded_at` | INTEGER |

Append-only — BR-006.

### `record_corrections`

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID string |
| `session_id` | TEXT FK | Completed session only (BR-009) |
| `original_set_log_id` | TEXT FK | Set log being corrected |
| `corrected_weight_kg` | REAL NULL | |
| `corrected_reps` | INTEGER NULL | |
| `reason` | TEXT | User-provided note |
| `created_at` | INTEGER | Epoch millis |

Append-only — BR-009. No `UPDATE`/`DELETE` DAO methods.

## Immutability Enforcement

- No `UPDATE`/`DELETE` DAO methods for rows where parent session `status = COMPLETED`
- Completed sessions and their set logs are insert-only from domain perspective

## DataStore Preferences

| Key | Type | Default |
|-----|------|---------|
| `rest_timer_seconds` | Int | 90 |
| `weight_unit_display` | String | `kg` |
| `catalog_seeded` | Boolean | false |

## Migrations

- Export schema: `exportSchema = true`
- Test migrations with Room Testing helper
- Never destructive migration in production
