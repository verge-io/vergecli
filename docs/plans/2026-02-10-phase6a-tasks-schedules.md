# Phase 6a: Tasks & Schedules Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg task` and `vrg task schedule` commands for task automation
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -30` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Tasks | `tasks` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/tasks.py` |
| Task Schedules | `task_schedules` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/task_schedules.py` |
| Schedule Triggers | `task_schedule_triggers` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/task_schedule_triggers.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/task_automation_example.py`

---

## Overview

Add task and schedule management commands. Tasks are the core unit of automation in VergeOS — they represent actions (snapshot, poweron, poweroff, etc.) bound to owner resources (VMs, tenants, etc.). Schedules define recurring time windows, and schedule triggers link tasks to schedules so they execute automatically.

The SDK exposes a `TaskScheduleTriggerManager` that bridges tasks and schedules. We expose this as `vrg task trigger` sub-commands.

## Commands

### `vrg task`

```
vrg task list [--filter ODATA] [--running] [--enabled | --disabled] [--status idle|running]
vrg task get <ID|NAME>
vrg task create --name NAME --owner OWNER_KEY --action ACTION [--table TABLE] [--description DESC] [--disabled] [--delete-after-run] [--settings-json JSON]
vrg task update <ID|NAME> [--name NAME] [--description DESC] [--enabled BOOL] [--delete-after-run BOOL] [--settings-json JSON]
vrg task delete <ID|NAME> [--yes]
vrg task enable <ID|NAME>
vrg task disable <ID|NAME>
vrg task run <ID|NAME> [--wait] [--timeout SECONDS] [--params-json JSON]
vrg task cancel <ID|NAME>
```

### `vrg task schedule`

```
vrg task schedule list [--filter ODATA] [--enabled | --disabled] [--repeat-every INTERVAL]
vrg task schedule get <ID|NAME>
vrg task schedule create --name NAME [--description DESC] [--disabled] [--repeat-every INTERVAL] [--repeat-iteration N] [--start-date DATE] [--end-date DATE] [--start-time SECONDS] [--end-time SECONDS] [--day-of-month OPTION] [--monday | --no-monday] ... [--sunday | --no-sunday]
vrg task schedule update <ID|NAME> [--name NAME] [--description DESC] [--enabled BOOL] [--repeat-every INTERVAL] [--repeat-iteration N] [--start-date DATE] [--end-date DATE] [--start-time SECONDS] [--end-time SECONDS] [--day-of-month OPTION] [--monday | --no-monday] ... [--sunday | --no-sunday]
vrg task schedule delete <ID|NAME> [--yes]
vrg task schedule enable <ID|NAME>
vrg task schedule disable <ID|NAME>
vrg task schedule show <ID|NAME> [--max-results N] [--start-time DATETIME] [--end-time DATETIME]
```

### `vrg task trigger`

```
vrg task trigger list <TASK>
vrg task trigger create <TASK> --schedule <SCHEDULE>
vrg task trigger delete <TRIGGER_ID> [--yes]
vrg task trigger run <TRIGGER_ID>
```

### Command Details

#### `vrg task list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--running` (flag) — show only running tasks
  - `--enabled` (flag) — show only enabled tasks
  - `--disabled` (flag) — show only disabled tasks (mutually exclusive with --enabled)
  - `--status` (str, choices: idle/running) — filter by status
- SDK: `tasks.list(status=..., running=..., enabled=...)` or convenience methods `list_running()`, `list_enabled()`, `list_disabled()`

#### `vrg task get`

- Positional: `TASK` (name or key)
- SDK: `tasks.get(key)` after `resolve_resource_id()`

#### `vrg task create`

- Required: `--name`, `--owner` (int key of owner resource), `--action` (str, e.g. "poweron", "snapshot")
- Optional:
  - `--table` (str) — owner resource type (e.g., "vms", "tenants"). SDK may auto-detect.
  - `--description` (str)
  - `--disabled` (flag, default enabled)
  - `--delete-after-run` (flag)
  - `--settings-json` (str) — JSON string for task settings/arguments
- Parse `--settings-json` to dict if provided
- SDK: `tasks.create(name=..., owner=..., action=..., table=..., description=..., enabled=..., delete_after_run=..., settings_args=...)`

#### `vrg task update`

- Positional: `TASK` (name or key)
- All fields optional
- SDK: `tasks.update(key, name=..., description=..., enabled=..., delete_after_run=..., settings_args=...)`

#### `vrg task delete`

- Positional: `TASK` (name or key)
- `--yes / -y` — skip confirmation
- SDK: `tasks.delete(key)`

#### `vrg task enable` / `vrg task disable`

- Positional: `TASK` (name or key)
- SDK: `tasks.enable(key)` / `tasks.disable(key)`

#### `vrg task run`

- Positional: `TASK` (name or key)
- Options:
  - `--wait / -w` (flag) — wait for task completion
  - `--timeout` (int, default 300) — wait timeout in seconds (only with --wait)
  - `--params-json` (str) — JSON string for execution parameters
- Parse `--params-json` to dict if provided, pass as `**params` to execute
- SDK: `tasks.execute(key, **params)`
- If `--wait`: `tasks.wait(key, timeout=timeout, raise_on_error=True)`
- Output success with task status after execution/wait

#### `vrg task cancel`

- Positional: `TASK` (name or key)
- SDK: `tasks.cancel(key)`
- Output success message

#### `vrg task schedule list`

- Options:
  - `--filter` (str)
  - `--enabled` / `--disabled` (mutually exclusive flags)
  - `--repeat-every` (str, choices: minute/hour/day/week/month/year/never) — filter by interval
- SDK: `task_schedules.list(enabled=..., repeat_every=...)`

#### `vrg task schedule get`

- Positional: `SCHEDULE` (name or key)
- SDK: `task_schedules.get(key)`

#### `vrg task schedule create`

- Required: `--name`
- Optional:
  - `--description` (str)
  - `--disabled` (flag)
  - `--repeat-every` (str, default "hour", choices: minute/hour/day/week/month/year/never)
  - `--repeat-iteration` (int, default 1) — run every N intervals
  - `--start-date` (str, YYYY-MM-DD)
  - `--end-date` (str, YYYY-MM-DD)
  - `--start-time` (int, seconds from midnight, default 0)
  - `--end-time` (int, seconds from midnight, default 86400)
  - `--day-of-month` (str, choices: first/last/15th/start_date, default "start_date")
  - Day-of-week flags: `--monday / --no-monday` through `--sunday / --no-sunday` (all default True)
- SDK: `task_schedules.create(name=..., description=..., enabled=..., repeat_every=..., ...)`

#### `vrg task schedule update`

- Positional: `SCHEDULE` (name or key)
- All fields optional, same as create
- SDK: `task_schedules.update(key, ...)`

#### `vrg task schedule delete`

- Positional: `SCHEDULE` (name or key)
- `--yes / -y` — skip confirmation
- Note: fails if schedule has active triggers (ConflictError)
- SDK: `task_schedules.delete(key)`

#### `vrg task schedule enable` / `vrg task schedule disable`

- Positional: `SCHEDULE` (name or key)
- SDK: `task_schedules.enable(key)` / `task_schedules.disable(key)`

#### `vrg task schedule show`

- Positional: `SCHEDULE` (name or key)
- Options:
  - `--max-results` (int, default 20) — number of upcoming executions to show
  - `--start-time` (str, datetime) — start of window
  - `--end-time` (str, datetime) — end of window
- SDK: `task_schedules.get_schedule(key, max_results=..., start_time=..., end_time=...)`
- Returns list of upcoming execution times — output as table

#### `vrg task trigger list`

- Positional: `TASK` (name or key)
- SDK: `tasks.triggers(task_key).list()` or `task_schedule_triggers.list_for_task(task_key)`

#### `vrg task trigger create`

- Positional: `TASK` (name or key)
- Required: `--schedule SCHEDULE` (name or key)
- Resolve both task and schedule
- SDK: `task_schedule_triggers.create(task=task_key, schedule=schedule_key)`

#### `vrg task trigger delete`

- Positional: `TRIGGER_ID` (numeric key)
- `--yes / -y` — skip confirmation
- SDK: `task_schedule_triggers.delete(key)`

#### `vrg task trigger run`

- Positional: `TRIGGER_ID` (numeric key)
- Manually fires the trigger (executes the linked task immediately)
- SDK: `task_schedule_triggers.trigger(key)`

## Files

### New Files

1. **`src/verge_cli/commands/task.py`**
   - Typer app with: list, get, create, update, delete, enable, disable, run, cancel
   - Helper: `_task_to_dict(task)` — convert SDK Task to output dict
   - Pattern: follow `vm.py` for CRUD + enable/disable, add run/cancel like power commands

2. **`src/verge_cli/commands/task_schedule.py`**
   - Typer app with: list, get, create, update, delete, enable, disable, show
   - Helper: `_schedule_to_dict(schedule)` — convert SDK TaskSchedule to output dict
   - Helper: `_upcoming_to_dict(entry)` — convert upcoming execution to output dict
   - Register as `app.add_typer(task_schedule.app, name="schedule")` on `task.app`

3. **`src/verge_cli/commands/task_trigger.py`**
   - Typer app with: list, create, delete, run
   - Helper: `_trigger_to_dict(trigger)` — convert SDK TaskScheduleTrigger to output dict
   - Register as `app.add_typer(task_trigger.app, name="trigger")` on `task.app`

4. **`tests/unit/test_task.py`**

5. **`tests/unit/test_task_schedule.py`**

6. **`tests/unit/test_task_trigger.py`**

### Modified Files

7. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import task`
   - Add: `app.add_typer(task.app, name="task")`

8. **`src/verge_cli/columns.py`**
   - Add `TASK_COLUMNS`, `TASK_SCHEDULE_COLUMNS`, `TASK_TRIGGER_COLUMNS`, `SCHEDULE_UPCOMING_COLUMNS`

9. **`tests/conftest.py`**
   - Add `mock_task`, `mock_task_schedule`, `mock_task_trigger` fixtures

## Column Definitions

```python
TASK_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("action_display", header="Action"),
    ColumnDef("owner_display", header="Owner"),
    ColumnDef("status", style_map={"running": "green", "idle": "dim", "error": "red bold"}),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    # wide-only
    ColumnDef("last_run", format_fn=format_epoch, wide_only=True),
    ColumnDef("progress", wide_only=True),
    ColumnDef("triggers_count", header="Triggers", wide_only=True),
    ColumnDef("events_count", header="Events", wide_only=True),
    ColumnDef("description", wide_only=True),
    ColumnDef("delete_after_run", header="Auto-Delete", format_fn=format_bool_yn, style_map=FLAG_STYLES, wide_only=True),
]

TASK_SCHEDULE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("repeat_display", header="Repeat"),
    ColumnDef("repeat_iteration", header="Every N"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("active_days", header="Days"),
    # wide-only
    ColumnDef("start_date", wide_only=True),
    ColumnDef("end_date", wide_only=True),
    ColumnDef("start_time_display", header="Start Time", wide_only=True),
    ColumnDef("end_time_display", header="End Time", wide_only=True),
    ColumnDef("day_of_month", header="Day of Month", wide_only=True),
    ColumnDef("description", wide_only=True),
]

TASK_TRIGGER_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("task_display", header="Task"),
    ColumnDef("schedule_display", header="Schedule"),
    ColumnDef("schedule_enabled", header="Sch Enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("schedule_repeat", header="Repeat"),
]

SCHEDULE_UPCOMING_COLUMNS = [
    ColumnDef("execution_time", header="Scheduled Time"),
]
```

## Data Mapping

```python
def _seconds_to_time(seconds: int) -> str:
    """Convert seconds from midnight to HH:MM format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

def _task_to_dict(task: Any) -> dict[str, Any]:
    return {
        "$key": int(task.key),
        "name": task.name,
        "description": task.get("description", ""),
        "status": task.status,
        "enabled": task.is_enabled,
        "action": task.get("action", ""),
        "action_display": task.action_display,
        "table": task.get("table", ""),
        "owner": task.get("owner"),
        "owner_display": task.owner_display,
        "creator_display": task.creator_display,
        "last_run": task.get("last_run"),
        "delete_after_run": task.is_delete_after_run,
        "system_created": task.is_system_created,
        "progress": task.progress,
        "error": task.get("error", ""),
        "triggers_count": task.trigger_count,
        "events_count": task.event_count,
    }

def _schedule_to_dict(schedule: Any) -> dict[str, Any]:
    return {
        "$key": int(schedule.key),
        "name": schedule.name,
        "description": schedule.get("description", ""),
        "enabled": schedule.is_enabled,
        "repeat_every": schedule.get("repeat_every", ""),
        "repeat_display": schedule.repeat_every_display,
        "repeat_iteration": schedule.repeat_count,
        "start_date": schedule.get("start_date", ""),
        "end_date": schedule.get("end_date", ""),
        "start_time_of_day": schedule.get("start_time_of_day", 0),
        "start_time_display": _seconds_to_time(schedule.get("start_time_of_day", 0)),
        "end_time_of_day": schedule.get("end_time_of_day", 86400),
        "end_time_display": _seconds_to_time(schedule.get("end_time_of_day", 86400)),
        "day_of_month": schedule.get("day_of_month", ""),
        "active_days": ", ".join(schedule.active_days),
    }

def _trigger_to_dict(trigger: Any) -> dict[str, Any]:
    return {
        "$key": int(trigger.key),
        "task_key": trigger.task_key,
        "task_display": trigger.task_display,
        "schedule_key": trigger.schedule_key,
        "schedule_display": trigger.schedule_display,
        "schedule_enabled": trigger.is_schedule_enabled,
        "schedule_repeat": trigger.schedule_repeat_every or "",
    }
```

## Test Plan

### Task Tests (`test_task.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_task_list` | Lists tasks |
| 2 | `test_task_list_running` | `--running` flag |
| 3 | `test_task_list_enabled` | `--enabled` filter |
| 4 | `test_task_list_disabled` | `--disabled` filter |
| 5 | `test_task_get` | Get by name |
| 6 | `test_task_get_by_key` | Get by numeric key |
| 7 | `test_task_create` | Basic create with required fields |
| 8 | `test_task_create_with_options` | All optional flags |
| 9 | `test_task_update` | Update name, description |
| 10 | `test_task_delete` | Delete with --yes |
| 11 | `test_task_delete_no_confirm` | Delete without --yes aborts |
| 12 | `test_task_enable` | Enable task |
| 13 | `test_task_disable` | Disable task |
| 14 | `test_task_run` | Execute task (no wait) |
| 15 | `test_task_run_with_wait` | Execute with --wait |
| 16 | `test_task_run_with_params` | Execute with --params-json |
| 17 | `test_task_cancel` | Cancel running task |
| 18 | `test_task_not_found` | Name resolution error (exit 6) |

### Task Schedule Tests (`test_task_schedule.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_schedule_list` | Lists schedules |
| 2 | `test_schedule_list_enabled` | `--enabled` filter |
| 3 | `test_schedule_list_by_repeat` | `--repeat-every day` filter |
| 4 | `test_schedule_get` | Get by name |
| 5 | `test_schedule_create_basic` | Create with defaults |
| 6 | `test_schedule_create_daily` | Daily schedule with time window |
| 7 | `test_schedule_create_weekly` | Weekly with specific days |
| 8 | `test_schedule_update` | Update interval and days |
| 9 | `test_schedule_delete` | Delete with --yes |
| 10 | `test_schedule_enable` | Enable schedule |
| 11 | `test_schedule_disable` | Disable schedule |
| 12 | `test_schedule_show` | Show upcoming executions |
| 13 | `test_schedule_show_max_results` | `--max-results` option |

### Task Trigger Tests (`test_task_trigger.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_trigger_list` | List triggers for a task |
| 2 | `test_trigger_create` | Create trigger linking task + schedule |
| 3 | `test_trigger_delete` | Delete with --yes |
| 4 | `test_trigger_run` | Manually fire trigger |

## Test Fixtures

```python
@pytest.fixture
def mock_task() -> MagicMock:
    task = MagicMock()
    task.key = 100
    task.name = "nightly-backup"
    task.status = "idle"
    task.is_enabled = True
    task.is_running = False
    task.is_complete = True
    task.has_error = False
    task.action_display = "Snapshot"
    task.owner_display = "web-server"
    task.creator_display = "admin"
    task.is_delete_after_run = False
    task.is_system_created = False
    task.progress = 0
    task.trigger_count = 1
    task.event_count = 0

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Nightly backup task",
            "action": "snapshot",
            "table": "vms",
            "owner": 1,
            "last_run": 1707200000,
            "error": "",
        }
        return data.get(key, default)

    task.get = mock_get
    return task

@pytest.fixture
def mock_task_schedule() -> MagicMock:
    schedule = MagicMock()
    schedule.key = 200
    schedule.name = "nightly-window"
    schedule.is_enabled = True
    schedule.repeat_every_display = "Day(s)"
    schedule.repeat_count = 1
    schedule.active_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Nightly maintenance window",
            "repeat_every": "day",
            "start_date": "2026-01-01",
            "end_date": "",
            "start_time_of_day": 7200,
            "end_time_of_day": 14400,
            "day_of_month": "start_date",
        }
        return data.get(key, default)

    schedule.get = mock_get
    return schedule

@pytest.fixture
def mock_task_trigger() -> MagicMock:
    trigger = MagicMock()
    trigger.key = 300
    trigger.task_key = 100
    trigger.task_display = "nightly-backup"
    trigger.schedule_key = 200
    trigger.schedule_display = "nightly-window"
    trigger.is_schedule_enabled = True
    trigger.schedule_repeat_every = "day"
    return trigger
```

## Task Checklist

- [x] Add `TASK_COLUMNS`, `TASK_SCHEDULE_COLUMNS`, `TASK_TRIGGER_COLUMNS`, `SCHEDULE_UPCOMING_COLUMNS` to `columns.py`
- [x] Add `mock_task`, `mock_task_schedule`, `mock_task_trigger` fixtures to `conftest.py`
- [x] Create `task.py` with all commands (list, get, create, update, delete, enable, disable, run, cancel)
- [x] Create `task_schedule.py` with all commands (list, get, create, update, delete, enable, disable, show)
- [x] Create `task_trigger.py` with all commands (list, create, delete, run)
- [x] Register `task.app` in `cli.py`, register schedule + trigger as sub-typers on task.app
- [x] Create `test_task.py` with all tests
- [x] Create `test_task_schedule.py` with all tests
- [x] Create `test_task_trigger.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
