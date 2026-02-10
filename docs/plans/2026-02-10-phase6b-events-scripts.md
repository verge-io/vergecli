# Phase 6b: Task Events & Scripts Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg task event` and `vrg task script` commands for event-driven automation and scripting
**Dependencies:** Phase 6a (`task.py` parent app must exist)
**Task Checklist:** Bottom of file — `tail -25` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Task Events | `task_events` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/task_events.py` |
| Task Scripts | `task_scripts` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/task_scripts.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/task_automation_example.py`

---

## Overview

Add event-driven task triggers and GCS script management. Task events fire tasks in response to system events (VM power-on, user login, errors, etc.) — they are the reactive counterpart to schedule-based triggers. Task scripts store reusable GCS (VergeOS scripting language) code that tasks can execute.

## Commands

### `vrg task event`

```
vrg task event list [--task TASK] [--table TABLE] [--event EVENT] [--filter ODATA]
vrg task event get <ID>
vrg task event create --task TASK --owner OWNER_KEY --event EVENT [--table TABLE] [--event-name NAME] [--filters-json JSON] [--context-json JSON]
vrg task event update <ID> [--filters-json JSON] [--context-json JSON]
vrg task event delete <ID> [--yes]
vrg task event trigger <ID> [--context-json JSON]
```

### `vrg task script`

```
vrg task script list [--filter ODATA]
vrg task script get <ID|NAME>
vrg task script create --name NAME --script FILE_OR_STRING [--description DESC] [--settings-json JSON]
vrg task script update <ID|NAME> [--name NAME] [--description DESC] [--script FILE_OR_STRING] [--settings-json JSON]
vrg task script delete <ID|NAME> [--yes]
vrg task script run <ID|NAME> [--params-json JSON]
```

### Command Details

#### `vrg task event list`

- Options:
  - `--task` (str) — filter by task (name or key). Resolve to key via `resolve_resource_id()`.
  - `--table` (str) — filter by resource table (e.g., "vms", "users")
  - `--event` (str) — filter by event type (e.g., "poweron", "login")
  - `--filter` (str) — OData filter
- SDK: `task_events.list(task=task_key, table=table, event=event)`

#### `vrg task event get`

- Positional: `ID` (numeric key — events don't have unique names)
- SDK: `task_events.get(key)`

#### `vrg task event create`

- Required:
  - `--task TASK` (str) — task to fire (name or key, resolved)
  - `--owner OWNER_KEY` (int) — owner resource key (the resource being watched)
  - `--event EVENT` (str) — event identifier (e.g., "poweron", "login", "error")
- Optional:
  - `--table TABLE` (str) — owner resource type (e.g., "vms"). SDK may auto-detect.
  - `--event-name NAME` (str) — human-readable event name
  - `--filters-json JSON` (str) — JSON string for table_event_filters
  - `--context-json JSON` (str) — JSON string for event context data
- Parse JSON strings to dicts
- SDK: `task_events.create(task=task_key, owner=owner_key, event=event, table=table, event_name=event_name, table_event_filters=filters, context=context)`

#### `vrg task event update`

- Positional: `ID` (numeric key)
- Optional:
  - `--filters-json` (str) — updated filter JSON
  - `--context-json` (str) — updated context JSON
- Note: only filters and context are updatable (task, owner, event are immutable)
- SDK: `task_events.update(key, table_event_filters=..., context=...)`

#### `vrg task event delete`

- Positional: `ID` (numeric key)
- `--yes / -y` — skip confirmation
- SDK: `task_events.delete(key)`

#### `vrg task event trigger`

- Positional: `ID` (numeric key)
- Optional: `--context-json` (str) — context data to pass to the triggered task
- Manually fires the event (executes the linked task)
- SDK: `task_events.trigger(key, context=context)`

#### `vrg task script list`

- Options: `--filter` (str) — OData filter
- SDK: `task_scripts.list()`

#### `vrg task script get`

- Positional: `SCRIPT` (name or key)
- SDK: `task_scripts.get(key)` after `resolve_resource_id()`
- Output includes the full script code

#### `vrg task script create`

- Required: `--name`, `--script`
- `--script` accepts either:
  - A file path (if it starts with `@` — e.g., `@/path/to/script.gcs`) — read file contents
  - A raw string (inline GCS code)
- Optional:
  - `--description` (str)
  - `--settings-json` (str) — JSON string for task_settings (script parameters/questions)
- SDK: `task_scripts.create(name=..., script=..., description=..., task_settings=...)`

#### `vrg task script update`

- Positional: `SCRIPT` (name or key)
- All fields optional
- `--script` accepts file path (`@path`) or raw string (same as create)
- SDK: `task_scripts.update(key, name=..., description=..., script=..., task_settings=...)`

#### `vrg task script delete`

- Positional: `SCRIPT` (name or key)
- `--yes / -y` — skip confirmation
- SDK: `task_scripts.delete(key)`

#### `vrg task script run`

- Positional: `SCRIPT` (name or key)
- Optional: `--params-json` (str) — JSON string for execution parameters
- Parse JSON to dict if provided, pass as `**params`
- SDK: `task_scripts.run(key, **params)`

## Design Decisions

### Script Input via `@file` Convention

The `--script` option supports two modes:
1. **Inline**: `--script 'log("Hello")'` — for short scripts
2. **File**: `--script @/path/to/script.gcs` — for longer scripts

Implementation:
```python
def _read_script_input(value: str) -> str:
    """Read script from file (@path) or return raw string."""
    if value.startswith("@"):
        path = Path(value[1:])
        if not path.exists():
            raise typer.BadParameter(f"Script file not found: {path}")
        return path.read_text()
    return value
```

This follows the `curl -d @file` convention that CLI users expect.

### Event Key-Only Lookups

Task events don't have unique names, so `get`, `update`, `delete`, and `trigger` all take numeric key only (no name resolution). List filtering is done via `--task`, `--table`, and `--event` options.

## Files

### New Files

1. **`src/verge_cli/commands/task_event.py`**
   - Typer app with: list, get, create, update, delete, trigger
   - Helper: `_event_to_dict(event)` — convert SDK TaskEvent to output dict
   - Register as `app.add_typer(task_event.app, name="event")` on `task.app`

2. **`src/verge_cli/commands/task_script.py`**
   - Typer app with: list, get, create, update, delete, run
   - Helper: `_script_to_dict(script)` — convert SDK TaskScript to output dict
   - Helper: `_read_script_input(value)` — handle `@file` or inline string
   - Register as `app.add_typer(task_script.app, name="script")` on `task.app`

3. **`tests/unit/test_task_event.py`**

4. **`tests/unit/test_task_script.py`**

### Modified Files

5. **`src/verge_cli/commands/task.py`** (from Phase 6a)
   - Add: `from verge_cli.commands import task_event, task_script`
   - Add: `app.add_typer(task_event.app, name="event")`
   - Add: `app.add_typer(task_script.app, name="script")`

6. **`src/verge_cli/columns.py`**
   - Add `TASK_EVENT_COLUMNS`, `TASK_SCRIPT_COLUMNS`

7. **`tests/conftest.py`**
   - Add `mock_task_event`, `mock_task_script` fixtures

## Column Definitions

```python
TASK_EVENT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("event", header="Event"),
    ColumnDef("event_name", header="Event Name"),
    ColumnDef("owner_display", header="Owner"),
    ColumnDef("table", header="Table"),
    ColumnDef("task_display", header="Task"),
    # wide-only
    ColumnDef("owner_key", header="Owner Key", wide_only=True),
    ColumnDef("task_key", header="Task Key", wide_only=True),
]

TASK_SCRIPT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description"),
    ColumnDef("task_count", header="Tasks"),
    # wide-only — script code is too long for table, show in get/json only
]
```

## Data Mapping

```python
def _event_to_dict(event: Any) -> dict[str, Any]:
    return {
        "$key": int(event.key),
        "event": event.event_type or "",
        "event_name": event.event_name_display or "",
        "owner_key": event.owner_key,
        "owner_display": event.owner_display,
        "table": event.owner_table or "",
        "task_key": event.task_key,
        "task_display": event.task_display,
        "filters": event.event_filters,
        "context": event.event_context,
    }

def _script_to_dict(script: Any) -> dict[str, Any]:
    return {
        "$key": int(script.key),
        "name": script.name,
        "description": script.get("description", ""),
        "script": script.script_code or "",
        "task_count": script.task_count,
        "settings": script.settings,
    }
```

## Test Plan

### Task Event Tests (`test_task_event.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_event_list` | Lists all events |
| 2 | `test_event_list_by_task` | `--task` filter resolves and passes |
| 3 | `test_event_list_by_table` | `--table vms` filter |
| 4 | `test_event_list_by_event` | `--event poweron` filter |
| 5 | `test_event_get` | Get by numeric key |
| 6 | `test_event_create` | Create with required fields |
| 7 | `test_event_create_with_options` | All optional fields |
| 8 | `test_event_update` | Update filters and context |
| 9 | `test_event_delete` | Delete with --yes |
| 10 | `test_event_delete_no_confirm` | Delete without --yes aborts |
| 11 | `test_event_trigger` | Manually trigger event |
| 12 | `test_event_trigger_with_context` | Trigger with --context-json |

### Task Script Tests (`test_task_script.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_script_list` | Lists scripts |
| 2 | `test_script_get` | Get by name |
| 3 | `test_script_get_by_key` | Get by numeric key |
| 4 | `test_script_create_inline` | Create with inline script string |
| 5 | `test_script_create_from_file` | Create with @file path |
| 6 | `test_script_create_file_not_found` | Error on missing @file |
| 7 | `test_script_create_with_options` | All optional fields |
| 8 | `test_script_update` | Update name and script |
| 9 | `test_script_update_from_file` | Update script from @file |
| 10 | `test_script_delete` | Delete with --yes |
| 11 | `test_script_delete_no_confirm` | Delete without --yes aborts |
| 12 | `test_script_run` | Run script |
| 13 | `test_script_run_with_params` | Run with --params-json |
| 14 | `test_script_not_found` | Name resolution error (exit 6) |

## Test Fixtures

```python
@pytest.fixture
def mock_task_event() -> MagicMock:
    event = MagicMock()
    event.key = 400
    event.event_type = "poweron"
    event.event_name_display = "Power On"
    event.owner_key = 1
    event.owner_display = "web-server"
    event.owner_table = "vms"
    event.task_key = 100
    event.task_display = "nightly-backup"
    event.event_filters = None
    event.event_context = None
    return event

@pytest.fixture
def mock_task_script() -> MagicMock:
    script = MagicMock()
    script.key = 500
    script.name = "cleanup-logs"
    script.script_code = 'log("Cleaning up old logs")\ndelete_old_files("/var/log", 30)'
    script.task_count = 2
    script.settings = None

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Cleans up log files older than 30 days",
        }
        return data.get(key, default)

    script.get = mock_get
    return script
```

## Task Checklist

- [x] Add `TASK_EVENT_COLUMNS`, `TASK_SCRIPT_COLUMNS` to `columns.py`
- [x] Add `mock_task_event`, `mock_task_script` fixtures to `conftest.py`
- [x] Create `task_event.py` with all commands (list, get, create, update, delete, trigger)
- [x] Create `task_script.py` with all commands (list, get, create, update, delete, run)
- [x] Register both as sub-typers on `task.app` in `task.py`
- [x] Create `test_task_event.py` with all tests
- [x] Create `test_task_script.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
