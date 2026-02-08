# Phase 3c: Snapshot Profiles Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg snapshot profile` commands for snapshot profile and period management
**Depends on:** Phase 3b (Cloud Snapshots) — requires `snapshot.py` to be created first

---

## Overview

Add snapshot profile management as a sub-resource of `vrg snapshot`, following the same nested pattern as tenant snapshots with periods. Snapshot profiles define scheduled backup policies with retention periods. The SDK exposes profiles via `client.snapshot_profiles` (SnapshotProfileManager) and periods via `profile_obj.periods` (SnapshotProfilePeriodManager).

## Commands

```
vrg snapshot profile list
vrg snapshot profile get <PROFILE>
vrg snapshot profile create --name NAME [--description DESC]
vrg snapshot profile update <PROFILE> [--name NAME] [--description DESC]
vrg snapshot profile delete <PROFILE> [--yes]

vrg snapshot profile period list <PROFILE>
vrg snapshot profile period get <PROFILE> <PERIOD>
vrg snapshot profile period create <PROFILE> --name NAME --frequency FREQ --retention SECS [options...]
vrg snapshot profile period update <PROFILE> <PERIOD> [options...]
vrg snapshot profile period delete <PROFILE> <PERIOD> [--yes]
```

### Profile Command Details

#### `list`
- Lists all snapshot profiles
- SDK: `client.snapshot_profiles.list()`

#### `get`
- Positional: `PROFILE` (name or key)
- Shows detailed profile info
- SDK: `client.snapshot_profiles.get(key)`

#### `create`
- Options:
  - `--name / -n` (required) — profile name
  - `--description / -d` (optional) — profile description
- SDK: `client.snapshot_profiles.create(name=..., description=...)`

#### `update`
- Positional: `PROFILE` (name or key)
- Options:
  - `--name` (optional) — new profile name
  - `--description` (optional) — new description
- SDK: `client.snapshot_profiles.update(key, name=..., description=...)`

#### `delete`
- Positional: `PROFILE` (name or key)
- Options: `--yes / -y` — skip confirmation
- SDK: `client.snapshot_profiles.delete(key)`

### Period Command Details

#### `list`
- Positional: `PROFILE` (name or key)
- Lists all periods for the specified profile
- SDK: `client.snapshot_profiles.periods(profile_key).list()`

#### `get`
- Positional: `PROFILE` (name or key), `PERIOD` (name or key)
- Shows detailed period info
- SDK: `client.snapshot_profiles.periods(profile_key).get(key)`

#### `create`
- Positional: `PROFILE` (name or key)
- Required Options:
  - `--name` — period name
  - `--frequency` — one of: `hourly`, `daily`, `weekly`, `monthly`, `yearly`
  - `--retention` — retention in seconds (0 = never expires)
- Optional Schedule Options:
  - `--minute` (int, 0-59, default 0) — minute of the hour
  - `--hour` (int, 0-23, default 0) — hour of the day
  - `--day-of-week` (str, default "any") — day of week (e.g., "monday", "tuesday", "any")
  - `--day-of-month` (int, 0-31, default 0) — day of the month (0 = any)
- Snapshot Options:
  - `--quiesce` (flag) — quiesce filesystem before snapshot
  - `--immutable` (flag) — make snapshots immutable
  - `--min-snapshots` (int, default 1) — minimum snapshots to keep
  - `--max-tier` (int, default 1) — maximum storage tier
  - `--skip-missed` (flag) — skip missed snapshot windows
- SDK: `client.snapshot_profiles.periods(profile_key).create(name=..., frequency=..., retention=..., ...)`

#### `update`
- Positional: `PROFILE`, `PERIOD`
- Options: same as create, all optional
- SDK: `client.snapshot_profiles.periods(profile_key).update(key, **kwargs)`

#### `delete`
- Positional: `PROFILE`, `PERIOD`
- Options: `--yes / -y` — skip confirmation
- SDK: `client.snapshot_profiles.periods(profile_key).delete(key)`

## Files

### New Files

1. **`src/verge_cli/commands/snapshot_profile_period.py`**
   - Pattern: mirror `tenant_snapshot.py` sub-resource pattern
   - Helper: `_get_profile()` — resolve profile and return (vctx, profile_key)
   - Helper: `_resolve_period()` — resolve period name/key to int key
   - Helper: `_period_to_dict()` — convert SDK object to output dict
   - Commands: list, get, create, update, delete

2. **`src/verge_cli/commands/snapshot_profile.py`**
   - Pattern: similar to `snapshot_profile_period.py` but registers period sub-typer
   - Helper: `_profile_to_dict()` — convert SDK object to output dict
   - Commands: list, get, create, update, delete
   - Registers: `period` sub-typer from `snapshot_profile_period.app`

3. **`tests/unit/test_snapshot_profile.py`**
   - Fixture: `mock_snapshot_profile` — MagicMock with key=800, name="daily-backup"
   - Tests: see test plan below

4. **`tests/unit/test_snapshot_profile_period.py`**
   - Fixture: `mock_snapshot_profile_period` — MagicMock with key=900, name="daily-midnight"
   - Tests: see test plan below

### Modified Files

5. **`src/verge_cli/commands/snapshot.py`**
   - Add: `from verge_cli.commands import snapshot_profile`
   - Add: `app.add_typer(snapshot_profile.app, name="profile")`
   - Note: This file must be created first in Phase 3b

6. **`src/verge_cli/columns.py`**
   - Add `SNAPSHOT_PROFILE_COLUMNS` definition
   - Add `SNAPSHOT_PROFILE_PERIOD_COLUMNS` definition

## Column Definitions

### Profiles

```python
SNAPSHOT_PROFILE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description", wide_only=True),
]
```

### Periods

```python
SNAPSHOT_PROFILE_PERIOD_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("frequency"),
    ColumnDef("retention", header="Retention (s)"),
    ColumnDef("min_snapshots", header="Min Snaps"),
    ColumnDef("max_tier", header="Max Tier"),
    # wide-only
    ColumnDef("minute", wide_only=True),
    ColumnDef("hour", wide_only=True),
    ColumnDef("day_of_week", header="Day of Week", wide_only=True),
    ColumnDef("quiesce", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("immutable", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("skip_missed", header="Skip Missed", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
]
```

## Data Mapping

### Profile

```python
def _profile_to_dict(profile: Any) -> dict[str, Any]:
    return {
        "$key": profile.key,
        "name": profile.name,
        "description": profile.get("description", ""),
    }
```

### Period

```python
def _period_to_dict(period: Any) -> dict[str, Any]:
    return {
        "$key": period.key,
        "name": period.name,
        "frequency": period.get("frequency"),
        "retention": period.get("retention"),
        "min_snapshots": period.get("min_snapshots"),
        "max_tier": period.get("max_tier"),
        "minute": period.get("minute"),
        "hour": period.get("hour"),
        "day_of_week": period.get("day_of_week", "any"),
        "quiesce": period.get("quiesce", False),
        "immutable": period.get("immutable", False),
        "skip_missed": period.get("skip_missed", False),
    }
```

## Test Plan

### Profile Tests (8)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_profile_list` | Lists all profiles |
| 2 | `test_profile_list_empty` | Handles empty list |
| 3 | `test_profile_get` | Get by name resolution |
| 4 | `test_profile_get_by_key` | Get by numeric key |
| 5 | `test_profile_create` | Basic create with name |
| 6 | `test_profile_update` | Update name and description |
| 7 | `test_profile_delete` | Delete with --yes |
| 8 | `test_profile_not_found` | Name resolution error (exit 6) |

### Period Tests (10)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_period_list` | Lists periods for a profile |
| 2 | `test_period_list_empty` | Handles empty period list |
| 3 | `test_period_get` | Get by name resolution |
| 4 | `test_period_get_by_key` | Get by numeric key |
| 5 | `test_period_create_daily` | Basic daily period creation |
| 6 | `test_period_create_hourly_with_options` | Create with schedule options |
| 7 | `test_period_update` | Update period options |
| 8 | `test_period_delete` | Delete with --yes |
| 9 | `test_period_not_found` | Period name resolution error (exit 6) |
| 10 | `test_period_profile_not_found` | Profile not found error (exit 6) |

## Implementation Steps

**Prerequisites:** Phase 3b must be complete with `snapshot.py` created.

1. Add `SNAPSHOT_PROFILE_COLUMNS` and `SNAPSHOT_PROFILE_PERIOD_COLUMNS` to `columns.py`
2. Create `snapshot_profile_period.py` with all period commands
3. Create `snapshot_profile.py` with all profile commands and period sub-typer registration
4. Register `profile` sub-typer in `snapshot.py`
5. Create `test_snapshot_profile_period.py` with all period tests
6. Create `test_snapshot_profile.py` with all profile tests
7. Run `uv run ruff check` and `uv run mypy src/verge_cli`
8. Run `uv run pytest tests/unit/test_snapshot_profile*.py -v`
9. Update PRD phase 3 checklist to mark snapshot profiles done
