# Phase 9b: System Log Management Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg log` commands — system audit/event log viewing with filtering and search
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| System Logs | `logs` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/logs.py` |

**SDK example:** None (read-only listing, follow `network_diag.py` pattern)

---

## Overview

Add system log viewing commands. System logs are the central audit trail in VergeOS — they record all operations across VMs, networks, nodes, users, and other resources. This is a read-only interface (no create/update/delete).

**SDK vs Release Plan corrections:**
- The release plan lists `clear` and `export` — the SDK has **no** `clear()` or `export()` methods on LogManager. System logs are immutable audit records.
- The SDK additionally offers: `search()`, `list_errors()`, `list_by_level()`, `list_by_object_type()`, `list_by_user()` — rich filtering capabilities.

**Key details:**
- Log keys are integers
- Default list limit is 100 (SDK default) — pass `--limit` to override
- Log timestamps are in **microseconds** — convert to seconds for `format_epoch`
- The `object_type` field maps API values (e.g., "vm", "vnet") to display names (e.g., "VM", "Network")
- Logs have property accessors like `level_display`, `object_type_display`, `created_at` (datetime), `timestamp_us` (raw)
- `search()` does text-based filtering of the `text` field

**Reference implementations:** `recipe_log.py` for log list/get pattern.

## Commands

```
vrg log list [--filter ODATA] [--level LEVEL] [--type OBJECT_TYPE] [--user USER] [--since DATETIME] [--before DATETIME] [--errors] [--limit N]
vrg log get <KEY>
vrg log search <TEXT> [--level LEVEL] [--type OBJECT_TYPE] [--since DATETIME] [--limit N]
```

### Command Details

#### `vrg log list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--level` (str) — filter by log level (critical/error/warning/message/audit)
  - `--type` (str) — filter by object type (vm, vnet, node, user, system, tenant, etc.)
  - `--user` (str) — filter by user who performed the action
  - `--since` (str) — show logs after this datetime (ISO format or relative like "1h", "2d")
  - `--before` (str) — show logs before this datetime
  - `--errors` (flag) — shortcut for `--level error` + critical (uses `list_errors()`)
  - `--limit` (int, default 100) — max results
- SDK routing:
  - `--errors`: `logs.list_errors(limit=limit, since=since)`
  - `--user X`: `logs.list_by_user(user=X, limit=limit, since=since)`
  - `--type X`: `logs.list_by_object_type(object_type=X, limit=limit, since=since)`
  - General: `logs.list(level=level, object_type=type, user=user, since=since, before=before, limit=limit)`

#### `vrg log get`

- Positional: `KEY` (numeric log entry key)
- SDK: `logs.get(key=int(key))`
- Note: logs don't have names — key only

#### `vrg log search`

- Positional: `TEXT` (search string to match in log message text)
- Options:
  - `--level` (str) — filter by log level
  - `--type` (str) — filter by object type
  - `--since` (str) — search after this datetime
  - `--limit` (int, default 100) — max results
- SDK: `logs.search(text=text, level=level, object_type=type, since=since, limit=limit)`

### Datetime Parsing

The `--since` and `--before` options accept:
1. ISO 8601 datetime strings: `"2026-02-10T12:00:00"`
2. Date-only strings: `"2026-02-10"` (parsed as midnight)

Implement a helper `_parse_datetime(value: str) -> datetime` that handles these formats. Keep it simple — don't over-engineer relative time parsing for MVP.

```python
from datetime import datetime

def _parse_datetime(value: str) -> datetime:
    """Parse a datetime string (ISO 8601 or date-only)."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise typer.BadParameter(f"Invalid datetime format: '{value}'. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")
```

## Files

### New Files

1. **`src/verge_cli/commands/log.py`** — Log list, get, search commands
   - Typer app with: list, get, search
   - Columns: `LOG_COLUMNS`
   - Helpers: `_log_to_dict()`, `_parse_datetime()`

2. **`tests/unit/test_log.py`** — Tests for all log commands

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import log`
   - Add: `app.add_typer(log.app, name="log")`

4. **`tests/conftest.py`**
   - Add `mock_log_entry` fixture

## Column Definition

### LOG_COLUMNS

```python
LOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level", style_map={
        "critical": "red bold", "error": "red",
        "warning": "yellow", "audit": "cyan",
        "message": "dim",
    }),
    ColumnDef("text", header="Message"),
    ColumnDef("object_type", header="Type"),
    ColumnDef("object_name", header="Object"),
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("user", wide_only=True),
]
```

## Data Mapping

```python
def _log_to_dict(log: Any) -> dict[str, Any]:
    # Log timestamps are in microseconds — convert to seconds for format_epoch
    ts = log.timestamp_us
    if isinstance(ts, (int, float)) and ts > 1e12:
        ts = ts / 1e6
    return {
        "$key": int(log.key),
        "level": log.level,
        "text": log.text,
        "object_type": log.object_type_display,
        "object_name": log.object_name,
        "timestamp": ts,
        "user": log.user,
    }
```

## Test Fixtures

```python
@pytest.fixture
def mock_log_entry() -> MagicMock:
    log = MagicMock()
    log.key = 1000
    log.level = "audit"
    log.level_display = "Audit"
    log.text = "VM 'web-server-01' started by admin"
    log.user = "admin"
    log.object_type = "vm"
    log.object_type_display = "VM"
    log.object_name = "web-server-01"
    log.timestamp_us = 1707000000000000  # microseconds
    log.created_at = datetime(2026, 2, 4, 0, 0, 0)
    return log
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_log_list` | Lists logs (default limit 100) |
| 2 | `test_log_list_with_limit` | `--limit 50` |
| 3 | `test_log_list_by_level` | `--level error` filter |
| 4 | `test_log_list_errors` | `--errors` shortcut uses `list_errors()` |
| 5 | `test_log_list_by_type` | `--type vm` filter |
| 6 | `test_log_list_by_user` | `--user admin` filter |
| 7 | `test_log_list_since` | `--since 2026-02-10` filter |
| 8 | `test_log_list_before` | `--before 2026-02-10T12:00:00` filter |
| 9 | `test_log_get` | Get log entry by key |
| 10 | `test_log_search` | Search by text |
| 11 | `test_log_search_with_level` | Search + `--level warning` |
| 12 | `test_log_search_with_type` | Search + `--type vm` |
| 13 | `test_log_search_with_since` | Search + `--since` |
| 14 | `test_parse_datetime_iso` | Parse "2026-02-10T12:00:00" |
| 15 | `test_parse_datetime_date_only` | Parse "2026-02-10" |
| 16 | `test_parse_datetime_invalid` | Invalid format raises BadParameter |

## Task Checklist

- [x] Create `log.py` with list, get, search commands + datetime helper
- [x] Register `log` in `cli.py`
- [x] Add `mock_log_entry` fixture to `conftest.py`
- [x] Create `test_log.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
