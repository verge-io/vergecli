# Phase 9a: Alarm Management Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg alarm` commands — alarm listing, filtering, snooze/resolve, and history
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Alarms | `alarms` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/alarms.py` |

**SDK example:** None (follow `system.py` pattern for singleton-like resources)

---

## Overview

Add alarm management commands for VergeOS monitoring. Alarms represent active alerts raised by the system for conditions like disk failures, high resource usage, connectivity issues, etc.

**SDK vs Release Plan corrections:**
- The release plan lists `acknowledge` and `clear` — the SDK has `snooze`, `unsnooze`, and `resolve` instead. No `acknowledge()` or `clear()` methods exist.
- The release plan lists `delete` — the SDK has no `delete()` method on AlarmManager. Alarms are resolved, not deleted.
- The SDK additionally offers: `list_critical()`, `list_errors()`, `list_warnings()`, `list_by_owner_type()`, `snooze_to()`, `list_history()`, `get_history()`, and `get_summary()`.

**Key details:**
- Alarms use integer keys
- Alarm `level` values: critical, error, warning, message, audit, summary, debug
- Alarm `owner_type` values: vms, vnets, nodes, tenant_nodes, users, system, cloud_snapshots
- Timestamps are Unix seconds (not microseconds like logs) — `created` and `modified` fields
- Snoozed alarms are hidden from list by default unless `--include-snoozed` is passed
- `AlarmHistory` is a separate list of resolved/lowered alarms (the archive)

**Reference implementations:** `recipe.py` for CRUD pattern, `recipe_log.py` for read-only list/get.

## Commands

```
vrg alarm list [--filter ODATA] [--level critical|error|warning] [--owner-type vms|vnets|nodes|...] [--include-snoozed]
vrg alarm get <ID>
vrg alarm snooze <ID> [--hours HOURS]
vrg alarm unsnooze <ID>
vrg alarm resolve <ID>
vrg alarm summary
vrg alarm history list [--filter ODATA] [--level LEVEL]
vrg alarm history get <ID>
```

### Command Details

#### `vrg alarm list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--level` (str) — filter by alarm level (critical/error/warning/message)
  - `--owner-type` (str) — filter by owner type (vms, vnets, nodes, tenant_nodes, users, system, cloud_snapshots)
  - `--include-snoozed` (flag) — include snoozed alarms (hidden by default)
  - `--limit` (int) — max results
- SDK routing:
  - No level filter: `alarms.list(include_snoozed=include_snoozed)`
  - `--level critical`: `alarms.list_critical(include_snoozed=include_snoozed)`
  - `--level error`: `alarms.list_errors(include_snoozed=include_snoozed)`
  - `--level warning`: `alarms.list_warnings(include_snoozed=include_snoozed)`
  - `--owner-type X`: `alarms.list_by_owner_type(owner_type=X, include_snoozed=include_snoozed)`
  - Otherwise: `alarms.list(level=level, include_snoozed=include_snoozed)`

#### `vrg alarm get`

- Positional: `ALARM` (numeric key)
- SDK: `alarms.get(key=int(alarm))`
- Note: alarms don't have unique names — use key only, no name resolution needed

#### `vrg alarm snooze`

- Positional: `ALARM` (numeric key)
- `--hours` (int, default 24) — snooze duration in hours
- SDK: `alarms.snooze(key, hours=hours)`
- Output: success message with snooze duration

#### `vrg alarm unsnooze`

- Positional: `ALARM` (numeric key)
- SDK: `alarms.unsnooze(key)`
- Output: success message

#### `vrg alarm resolve`

- Positional: `ALARM` (numeric key)
- SDK: `alarms.resolve(key)`
- Output: success message
- Note: only resolvable alarms can be resolved — the SDK will raise an error for non-resolvable ones

#### `vrg alarm summary`

- No arguments — shows aggregate alarm counts by level
- SDK: `alarms.get_summary()` → returns dict with counts
- Output: summary table showing critical/error/warning counts

#### `vrg alarm history list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--level` (str) — filter by alarm level
  - `--limit` (int) — max results
- SDK: `alarms.list_history(level=level, limit=limit)`

#### `vrg alarm history get`

- Positional: `KEY` (numeric key)
- SDK: `alarms.get_history(key)`

## Files

### New Files

1. **`src/verge_cli/commands/alarm.py`** — Alarm commands + alarm history sub-command
   - Typer app with: list, get, snooze, unsnooze, resolve, summary
   - Registers `alarm_history.app` as sub-command `history`
   - Columns: `ALARM_COLUMNS`, `ALARM_SUMMARY_COLUMNS`
   - Helper: `_alarm_to_dict()`

2. **`src/verge_cli/commands/alarm_history.py`** — Alarm history list + get
   - Columns: `ALARM_HISTORY_COLUMNS`
   - Helper: `_history_to_dict()`

3. **`tests/unit/test_alarm.py`** — Tests for alarm commands

4. **`tests/unit/test_alarm_history.py`** — Tests for alarm history commands

### Modified Files

5. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import alarm`
   - Add: `app.add_typer(alarm.app, name="alarm")`

6. **`tests/conftest.py`**
   - Add `mock_alarm` fixture
   - Add `mock_alarm_history` fixture

## Column Definitions

### ALARM_COLUMNS

```python
ALARM_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level", style_map={
        "critical": "red bold", "error": "red",
        "warning": "yellow", "message": "dim",
    }),
    ColumnDef("alarm_type", header="Type"),
    ColumnDef("status"),
    ColumnDef("owner_type", header="Owner Type"),
    ColumnDef("owner_name", header="Owner"),
    ColumnDef("created_at", header="Created", format_fn=format_epoch),
    # wide-only
    ColumnDef("alarm_id", header="Alarm ID", wide_only=True),
    ColumnDef("description", wide_only=True),
    ColumnDef("is_snoozed", header="Snoozed", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("is_resolvable", header="Resolvable", format_fn=format_bool_yn, wide_only=True),
]
```

### ALARM_HISTORY_COLUMNS

```python
ALARM_HISTORY_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level", style_map={
        "critical": "red bold", "error": "red",
        "warning": "yellow", "message": "dim",
    }),
    ColumnDef("alarm_type", header="Type"),
    ColumnDef("status"),
    ColumnDef("owner"),
    ColumnDef("raised_at", header="Raised", format_fn=format_epoch),
    ColumnDef("lowered_at", header="Lowered", format_fn=format_epoch),
    ColumnDef("archived_by", header="Archived By", wide_only=True),
    ColumnDef("alarm_id", header="Alarm ID", wide_only=True),
]
```

## Data Mappings

```python
def _alarm_to_dict(alarm: Any) -> dict[str, Any]:
    return {
        "$key": int(alarm.key),
        "level": alarm.level,
        "alarm_type": alarm.alarm_type,
        "alarm_id": alarm.alarm_id,
        "status": alarm.status,
        "description": alarm.description,
        "owner_type": alarm.owner_type_display,
        "owner_name": alarm.owner_name,
        "is_resolvable": alarm.is_resolvable,
        "resolve_text": alarm.resolve_text,
        "is_snoozed": alarm.is_snoozed,
        "snoozed_by": alarm.snoozed_by,
        "created_at": alarm.created_at.timestamp() if alarm.created_at else None,
    }

def _history_to_dict(entry: Any) -> dict[str, Any]:
    return {
        "$key": int(entry.key),
        "level": entry.level,
        "alarm_type": entry.alarm_type,
        "alarm_id": entry.alarm_id,
        "status": entry.status,
        "owner": entry.owner,
        "archived_by": entry.archived_by,
        "raised_at": entry.raised_at.timestamp() if entry.raised_at else None,
        "lowered_at": entry.lowered_at.timestamp() if entry.lowered_at else None,
    }
```

## Test Fixtures

```python
@pytest.fixture
def mock_alarm() -> MagicMock:
    alarm = MagicMock()
    alarm.key = 42
    alarm.level = "warning"
    alarm.level_display = "Warning"
    alarm.alarm_type = "High CPU Usage"
    alarm.alarm_id = "a1b2c3d4"
    alarm.status = "CPU usage above 90% for 15 minutes"
    alarm.description = "Triggered when CPU usage exceeds threshold"
    alarm.owner_type = "vms"
    alarm.owner_type_display = "VM"
    alarm.owner_name = "web-server-01"
    alarm.owner_key = 10
    alarm.is_resolvable = True
    alarm.resolve_text = "Reduce CPU load or add resources"
    alarm.is_snoozed = False
    alarm.snoozed_by = ""
    alarm.snooze_until = None
    alarm.created_at = datetime(2026, 2, 10, 12, 0, 0)
    alarm.modified_at = datetime(2026, 2, 10, 12, 0, 0)
    return alarm

@pytest.fixture
def mock_alarm_history() -> MagicMock:
    entry = MagicMock()
    entry.key = 100
    entry.level = "error"
    entry.level_display = "Error"
    entry.alarm_type = "Disk Failure"
    entry.alarm_id = "e5f6g7h8"
    entry.status = "Disk /dev/sdb failed"
    entry.owner = "node-01"
    entry.archived_by = "auto"
    entry.raised_at = datetime(2026, 2, 8, 10, 0, 0)
    entry.lowered_at = datetime(2026, 2, 8, 14, 0, 0)
    return entry
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_alarm_list` | Lists active alarms |
| 2 | `test_alarm_list_critical` | `--level critical` uses `list_critical()` |
| 3 | `test_alarm_list_errors` | `--level error` uses `list_errors()` |
| 4 | `test_alarm_list_warnings` | `--level warning` uses `list_warnings()` |
| 5 | `test_alarm_list_by_owner_type` | `--owner-type vms` filter |
| 6 | `test_alarm_list_include_snoozed` | `--include-snoozed` flag |
| 7 | `test_alarm_get` | Get alarm by key |
| 8 | `test_alarm_snooze_default` | Snooze with default 24 hours |
| 9 | `test_alarm_snooze_custom` | Snooze with `--hours 48` |
| 10 | `test_alarm_unsnooze` | Unsnooze alarm |
| 11 | `test_alarm_resolve` | Resolve alarm |
| 12 | `test_alarm_summary` | Show alarm summary |
| 13 | `test_alarm_history_list` | List alarm history |
| 14 | `test_alarm_history_list_by_level` | `--level error` filter |
| 15 | `test_alarm_history_get` | Get history entry |

## Task Checklist

- [x] Create `alarm.py` with list, get, snooze, unsnooze, resolve, summary commands
- [x] Create `alarm_history.py` with list + get commands
- [x] Register `alarm_history` as sub-command of `alarm`
- [x] Register `alarm` in `cli.py`
- [x] Add `mock_alarm` and `mock_alarm_history` fixtures to `conftest.py`
- [x] Create `test_alarm.py`
- [x] Create `test_alarm_history.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
