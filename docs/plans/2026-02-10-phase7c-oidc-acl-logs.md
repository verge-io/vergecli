# Phase 7c: OIDC Access Control & Logs Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg oidc user`, `vrg oidc group`, and `vrg oidc log` sub-commands
**Dependencies:** Phase 7b (`oidc.py` parent app must exist)
**Task Checklist:** Bottom of file — `tail -25` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| OIDC App Users | `oidc_application_users` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/oidc_applications.py` |
| OIDC App Groups | `oidc_application_groups` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/oidc_applications.py` |
| OIDC App Logs | `oidc_application_logs` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/oidc_applications.py` |

**SDK example:** None (follow `vm_nic.py` sub-resource pattern)

---

## Overview

Add OIDC application sub-resource management: user ACL, group ACL, and application logs. When an OIDC application has `restrict_access=True`, only explicitly allowed users and groups can authenticate. Logs provide audit trails of OIDC authentication events.

All three sub-resources are scoped to a parent OIDC application — every command takes the parent `APP` as the first positional argument.

**Depends on:** Phase 7b (OIDC core commands and `oidc.app` Typer must exist).

## Commands

### `vrg oidc user`

```
vrg oidc user list <APP>
vrg oidc user add <APP> <USER>
vrg oidc user remove <APP> <USER|ENTRY_KEY> [--yes]
```

### `vrg oidc group`

```
vrg oidc group list <APP>
vrg oidc group add <APP> <GROUP>
vrg oidc group remove <APP> <GROUP|ENTRY_KEY> [--yes]
```

### `vrg oidc log`

```
vrg oidc log list <APP> [--level audit|message|warning|error|critical] [--errors] [--warnings] [--limit N]
vrg oidc log get <APP> <LOG_ID>
```

### Command Details

#### `vrg oidc user list`

- Positional: `APP` (OIDC application name or key)
- Resolve APP, then get scoped user manager
- SDK: `oidc_applications.allowed_users(app_key).list()`
- Shows: user name, user key, ACL entry key

#### `vrg oidc user add`

- Positional: `APP` (name or key), `USER` (user name or key)
- Resolve both APP and USER
- SDK: `oidc_applications.allowed_users(app_key).add(user_key=user_key)`
- Output success with user name

#### `vrg oidc user remove`

- Positional: `APP` (name or key), `USER_OR_KEY` (user name/key OR ACL entry key)
- `--yes / -y` — skip confirmation
- Resolution strategy:
  1. If numeric — could be user key or ACL entry key. Try to find ACL entry by listing and matching user key first.
  2. If string — resolve as user name, then find the ACL entry for that user.
- To find ACL entry: list all entries for the app, find the one matching the user key
- SDK: `oidc_applications.allowed_users(app_key).delete(entry_key)`

#### `vrg oidc group list`

- Positional: `APP` (name or key)
- SDK: `oidc_applications.allowed_groups(app_key).list()`
- Shows: group name, group key, ACL entry key

#### `vrg oidc group add`

- Positional: `APP` (name or key), `GROUP` (group name or key)
- Resolve both APP and GROUP
- SDK: `oidc_applications.allowed_groups(app_key).add(group_key=group_key)`

#### `vrg oidc group remove`

- Positional: `APP` (name or key), `GROUP_OR_KEY` (group name/key OR ACL entry key)
- `--yes / -y` — skip confirmation
- Same resolution strategy as user remove
- SDK: `oidc_applications.allowed_groups(app_key).delete(entry_key)`

#### `vrg oidc log list`

- Positional: `APP` (name or key)
- Options:
  - `--level` (str, choices: audit/message/warning/error/critical) — filter by log level
  - `--errors` (flag) — shorthand for `--level error` (includes error + critical)
  - `--warnings` (flag) — shorthand for `--level warning`
  - `--limit` (int, default 50) — max number of log entries
- SDK:
  - `oidc_applications.logs(app_key).list(level=level, limit=limit)`
  - `oidc_applications.logs(app_key).list_errors(limit=limit)` for --errors
  - `oidc_applications.logs(app_key).list_warnings(limit=limit)` for --warnings
  - `oidc_applications.logs(app_key).list_audits(limit=limit)` for --level audit
- Logs are sorted by timestamp descending (newest first)

#### `vrg oidc log get`

- Positional: `APP` (name or key), `LOG_ID` (numeric key)
- SDK: `oidc_applications.logs(app_key).get(key=log_id)`

## Design Decisions

### Remove by User/Group Name

The ACL entries have their own `$key`, but users think in terms of "remove user X from app Y", not "delete ACL entry 42". We support both:
1. By user/group name: resolve the name to a key, list ACL entries, find the matching one, delete it
2. By ACL entry key: if the identifier is numeric and doesn't match any user/group, treat it as an ACL entry key directly

Implementation for the lookup:

```python
def _find_acl_entry(entries: list, member_key: int, member_field: str) -> int:
    """Find ACL entry key by member key."""
    for entry in entries:
        if getattr(entry, member_field) == member_key:
            return int(entry.key)
    raise NotFoundError(f"No ACL entry found for key {member_key}")
```

### Log Timestamp Formatting

OIDC log timestamps are in microseconds (not seconds). We need a format function:

```python
def format_microseconds(value: Any, *, for_csv: bool = False) -> str:
    """Format microsecond timestamp as datetime string."""
    if value is None:
        return "" if for_csv else "-"
    if isinstance(value, (int, float)) and value > 0:
        dt = datetime.fromtimestamp(value / 1_000_000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)
```

### Sub-Typer Registration

These sub-commands register on the `oidc.app` Typer from Phase 7b:

```python
# In oidc.py (modified)
from verge_cli.commands import oidc_user, oidc_group, oidc_log
app.add_typer(oidc_user.app, name="user")
app.add_typer(oidc_group.app, name="group")
app.add_typer(oidc_log.app, name="log")
```

## Files

### New Files

1. **`src/verge_cli/commands/oidc_user.py`**
   - Typer app with: list, add, remove
   - Helper: `_oidc_user_to_dict(entry)` — convert ACL entry to output dict
   - Helper: `_resolve_app()` — resolve OIDC app identifier

2. **`src/verge_cli/commands/oidc_group.py`**
   - Typer app with: list, add, remove
   - Helper: `_oidc_group_to_dict(entry)` — convert ACL entry to output dict

3. **`src/verge_cli/commands/oidc_log.py`**
   - Typer app with: list, get
   - Helper: `_oidc_log_to_dict(log)` — convert log entry to output dict

4. **`tests/unit/test_oidc_user.py`**

5. **`tests/unit/test_oidc_group.py`**

6. **`tests/unit/test_oidc_log.py`**

### Modified Files

7. **`src/verge_cli/commands/oidc.py`** (from Phase 7b)
   - Add: `from verge_cli.commands import oidc_user, oidc_group, oidc_log`
   - Add: `app.add_typer(oidc_user.app, name="user")`
   - Add: `app.add_typer(oidc_group.app, name="group")`
   - Add: `app.add_typer(oidc_log.app, name="log")`

8. **`src/verge_cli/columns.py`**
   - Add `OIDC_USER_COLUMNS`, `OIDC_GROUP_COLUMNS`, `OIDC_LOG_COLUMNS`
   - Add `format_microseconds` helper (or add to existing helpers)

9. **`tests/conftest.py`**
   - Add `mock_oidc_user_entry`, `mock_oidc_group_entry`, `mock_oidc_log` fixtures

## Column Definitions

```python
OIDC_USER_COLUMNS = [
    ColumnDef("$key", header="Entry Key"),
    ColumnDef("user_display", header="User"),
    ColumnDef("user_key", header="User Key"),
]

OIDC_GROUP_COLUMNS = [
    ColumnDef("$key", header="Entry Key"),
    ColumnDef("group_display", header="Group"),
    ColumnDef("group_key", header="Group Key"),
]

OIDC_LOG_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("timestamp", format_fn=format_microseconds),
    ColumnDef(
        "level",
        style_map={
            "audit": "cyan",
            "message": "dim",
            "warning": "yellow",
            "error": "red bold",
            "critical": "red bold",
        },
    ),
    ColumnDef("text", header="Message"),
    # wide-only
    ColumnDef("user_display", header="User", wide_only=True),
]
```

## Data Mapping

```python
def _oidc_user_to_dict(entry: Any) -> dict[str, Any]:
    return {
        "$key": int(entry.key),
        "user_key": entry.get("user"),
        "user_display": entry.get("user_display", ""),
    }

def _oidc_group_to_dict(entry: Any) -> dict[str, Any]:
    return {
        "$key": int(entry.key),
        "group_key": entry.get("group"),
        "group_display": entry.get("group_display", ""),
    }

def _oidc_log_to_dict(log: Any) -> dict[str, Any]:
    return {
        "$key": int(log.key),
        "timestamp": log.get("timestamp"),
        "level": log.get("level", ""),
        "text": log.get("text", ""),
        "user": log.get("user"),
        "user_display": log.get("user_display", ""),
        "application_key": log.application_key,
        "is_error": log.is_error,
        "is_warning": log.is_warning,
    }
```

## Test Plan

### OIDC User ACL Tests (`test_oidc_user.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_oidc_user_list` | Lists allowed users for an app |
| 2 | `test_oidc_user_list_empty` | Empty ACL |
| 3 | `test_oidc_user_add` | Add user to allowed list |
| 4 | `test_oidc_user_add_by_name` | Add user by username (resolved) |
| 5 | `test_oidc_user_remove` | Remove user by name |
| 6 | `test_oidc_user_remove_by_entry_key` | Remove by ACL entry key |
| 7 | `test_oidc_user_remove_no_confirm` | Remove without --yes aborts |
| 8 | `test_oidc_user_app_not_found` | Parent app resolution error (exit 6) |

### OIDC Group ACL Tests (`test_oidc_group.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_oidc_group_list` | Lists allowed groups |
| 2 | `test_oidc_group_add` | Add group to allowed list |
| 3 | `test_oidc_group_add_by_name` | Add group by name (resolved) |
| 4 | `test_oidc_group_remove` | Remove group |
| 5 | `test_oidc_group_remove_no_confirm` | Remove without --yes aborts |

### OIDC Log Tests (`test_oidc_log.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_oidc_log_list` | Lists logs for an app |
| 2 | `test_oidc_log_list_errors` | `--errors` filter |
| 3 | `test_oidc_log_list_warnings` | `--warnings` filter |
| 4 | `test_oidc_log_list_by_level` | `--level audit` filter |
| 5 | `test_oidc_log_list_limit` | `--limit 10` |
| 6 | `test_oidc_log_get` | Get specific log entry |

## Test Fixtures

```python
@pytest.fixture
def mock_oidc_user_entry() -> MagicMock:
    entry = MagicMock()
    entry.key = 90

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "user": 10,
            "user_display": "admin",
            "oidc_application": 80,
        }
        return data.get(key, default)

    entry.get = mock_get
    return entry

@pytest.fixture
def mock_oidc_group_entry() -> MagicMock:
    entry = MagicMock()
    entry.key = 91

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "group": 20,
            "group_display": "admins",
            "oidc_application": 80,
        }
        return data.get(key, default)

    entry.get = mock_get
    return entry

@pytest.fixture
def mock_oidc_log() -> MagicMock:
    log = MagicMock()
    log.key = 1000
    log.application_key = 80
    log.is_error = False
    log.is_warning = False

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "timestamp": 1707100000000000,  # microseconds
            "level": "audit",
            "text": "User admin authenticated successfully",
            "user": 10,
            "user_display": "admin",
        }
        return data.get(key, default)

    log.get = mock_get
    return log
```

## Task Checklist

- [x] Add `OIDC_USER_COLUMNS`, `OIDC_GROUP_COLUMNS`, `OIDC_LOG_COLUMNS` to `columns.py`
- [x] Add `format_microseconds` helper to `columns.py`
- [x] Add `mock_oidc_user_entry`, `mock_oidc_group_entry`, `mock_oidc_log` fixtures to `conftest.py`
- [x] Create `oidc_user.py` with all commands (list, add, remove)
- [x] Create `oidc_group.py` with all commands (list, add, remove)
- [x] Create `oidc_log.py` with all commands (list, get)
- [x] Register all three as sub-typers on `oidc.app` in `oidc.py`
- [x] Create `test_oidc_user.py` with all tests
- [x] Create `test_oidc_group.py` with all tests
- [x] Create `test_oidc_log.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
