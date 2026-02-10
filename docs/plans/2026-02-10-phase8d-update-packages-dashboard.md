# Phase 8d: Update Packages, Branches, Dashboard & Logs Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg update branch`, `vrg update package`, `vrg update available`, `vrg update status`, `vrg update log` — read-only info/monitoring commands
**Dependencies:** Phase 8c (`update.py` parent app must exist)
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Update Branches | `update_branches` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |
| Installed Packages | `update_packages` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |
| Available Packages | `update_source_packages` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |
| Update Logs | `update_logs` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |
| Update Dashboard | `update_dashboard` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |

**SDK example:** None (read-only listing commands, follow `network_diag.py` pattern)

---

## Overview

Add the read-only informational sub-commands for system updates. These are all listing/viewing commands — no CRUD mutations. They let admins see what branches, packages, and updates are available, view the update dashboard summary, and browse update logs.

**Key details:**
- `UpdatePackage` keys are **strings** (package names), not integers — use name-based lookup
- `UpdateBranch` is read-only (list + get only)
- `UpdateSourcePackage` ("available packages") supports convenient filter methods: `list_pending()`, `list_downloaded()`
- `UpdateDashboard` is a singleton aggregate — `get()` takes no key
- All commands in this plan are read-only — no confirmation prompts needed

**Reference implementations:** `recipe_log.py` for read-only list/get pattern.

## Commands

```
vrg update branch list [--filter ODATA]
vrg update branch get <ID|NAME>
vrg update package list [--filter ODATA] [--branch BRANCH]
vrg update package get <NAME>
vrg update available list [--source SOURCE] [--branch BRANCH] [--downloaded | --pending]
vrg update available get <ID|NAME>
vrg update status
vrg update log list [--level LEVEL]
vrg update log get <KEY>
```

### Command Details

#### `vrg update branch list`

- Options:
  - `--filter` (str) — OData filter expression
- Read-only list of available update branches (e.g., stable-4.13, beta)
- SDK: `update_branches.list()`

#### `vrg update branch get`

- Positional: `BRANCH` (numeric key or name)
- Resolution: `resolve_resource_id(client.update_branches, identifier, "Update branch")`
- SDK: `update_branches.get(key)`

#### `vrg update package list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--branch` (str) — filter by branch name or key
- Lists currently installed packages
- SDK: `update_packages.list(branch=branch_key)`

#### `vrg update package get`

- Positional: `NAME` (package name string — this is the key)
- Note: package keys are strings, not integers. Pass the name directly as key.
- SDK: `update_packages.get(key=name)` or `update_packages.get(name=name)`

#### `vrg update available list`

- Options:
  - `--source` (str) — filter by source name or key
  - `--branch` (str) — filter by branch name or key
  - `--downloaded` (flag) — show only downloaded packages
  - `--pending` (flag) — show only pending (not yet downloaded) packages
- Lists packages available from update sources
- SDK:
  - Default: `update_source_packages.list(source=source_key, branch=branch_key)`
  - `--downloaded`: `update_source_packages.list_downloaded()`
  - `--pending`: `update_source_packages.list_pending()`
- `--downloaded` and `--pending` are mutually exclusive

#### `vrg update available get`

- Positional: `PACKAGE` (numeric key or name)
- SDK: `update_source_packages.get(key)` or `update_source_packages.get(name=name)`

#### `vrg update status`

- No arguments — displays the update dashboard summary
- SDK: `update_dashboard.get()` → `UpdateDashboard`
- Output: aggregated view showing settings, package counts, recent logs
- Consider formatting as multiple sections or a summary table

#### `vrg update log list`

- Options:
  - `--level` (str) — filter by log level (audit/message/warning/error/critical)
- SDK: `update_logs.list(level=level)`

#### `vrg update log get`

- Positional: `KEY` (numeric log entry key)
- SDK: `update_logs.get(key)`

## Files

### New Files

1. **`src/verge_cli/commands/update_branch.py`** — Branch list + get
   - Columns: `BRANCH_COLUMNS`
   - Helper: `_branch_to_dict()`

2. **`src/verge_cli/commands/update_package.py`** — Installed package list + get
   - Columns: `PACKAGE_COLUMNS`
   - Helper: `_package_to_dict()`

3. **`src/verge_cli/commands/update_available.py`** — Available package list + get
   - Columns: `AVAILABLE_COLUMNS`
   - Helper: `_available_to_dict()`

4. **`src/verge_cli/commands/update_log.py`** — Update log list + get
   - Columns: `UPDATE_LOG_COLUMNS`
   - Helper: `_log_to_dict()`

5. **`tests/unit/test_update_branch.py`**

6. **`tests/unit/test_update_package.py`**

7. **`tests/unit/test_update_available.py`**

8. **`tests/unit/test_update_log.py`**

### Modified Files

9. **`src/verge_cli/commands/update.py`** (created in 8c)
   - Register sub-commands: `branch`, `package`, `available`, `log`
   - Add `status` command (update dashboard)
   - Add: `DASHBOARD_COLUMNS`, `_dashboard_to_dict()`

10. **`tests/conftest.py`**
    - Add `mock_update_branch` fixture
    - Add `mock_update_package` fixture
    - Add `mock_update_source_package` fixture
    - Add `mock_update_log` fixture
    - Add `mock_update_dashboard` fixture

## Column Definitions

### BRANCH_COLUMNS

```python
BRANCH_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description"),
    ColumnDef("created", wide_only=True),
]
```

### PACKAGE_COLUMNS

```python
PACKAGE_COLUMNS: list[ColumnDef] = [
    ColumnDef("name"),
    ColumnDef("version"),
    ColumnDef("type"),
    ColumnDef("optional", format_fn=format_bool_yn),
    ColumnDef("description", wide_only=True),
    ColumnDef("branch", wide_only=True),
    ColumnDef("modified", wide_only=True),
]
```

### AVAILABLE_COLUMNS

```python
AVAILABLE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("version"),
    ColumnDef("downloaded", format_fn=format_bool_yn, style_map={"Y": "green", "-": "dim"}),
    ColumnDef("optional", format_fn=format_bool_yn),
    ColumnDef("description", wide_only=True),
    ColumnDef("branch", wide_only=True),
    ColumnDef("source", wide_only=True),
]
```

### UPDATE_LOG_COLUMNS

```python
UPDATE_LOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level", style_map={"error": "red", "warning": "yellow", "critical": "red bold", "audit": "cyan"}),
    ColumnDef("text", header="Message"),
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("object_name", header="Object", wide_only=True),
    ColumnDef("user", wide_only=True),
]
```

## Data Mappings

```python
def _branch_to_dict(branch: Any) -> dict[str, Any]:
    return {
        "$key": int(branch.key),
        "name": branch.name,
        "description": branch.get("description", ""),
        "created": branch.get("created", ""),
    }

def _package_to_dict(pkg: Any) -> dict[str, Any]:
    return {
        "name": pkg.name,
        "version": pkg.get("version", ""),
        "type": pkg.get("type", ""),
        "optional": pkg.get("optional"),
        "description": pkg.get("description", ""),
        "branch": pkg.get("branch", ""),
        "modified": pkg.get("modified", ""),
    }

def _available_to_dict(pkg: Any) -> dict[str, Any]:
    return {
        "$key": int(pkg.key),
        "name": pkg.name,
        "version": pkg.get("version", ""),
        "downloaded": pkg.get("downloaded"),
        "optional": pkg.get("optional"),
        "description": pkg.get("description", ""),
        "branch": pkg.get("branch", ""),
        "source": pkg.get("source", ""),
    }

def _log_to_dict(log: Any) -> dict[str, Any]:
    ts = log.get("timestamp")
    if isinstance(ts, (int, float)) and ts > 1e12:
        ts = ts / 1e6
    return {
        "$key": int(log.key),
        "level": log.get("level", ""),
        "text": log.get("text", ""),
        "timestamp": ts,
        "object_name": log.get("object_name", ""),
        "user": log.get("user", ""),
    }

def _dashboard_to_dict(dashboard: Any) -> dict[str, Any]:
    return {
        "node_count": dashboard.get("node_count", 0),
        "event_count": dashboard.get("counts", {}).get("event_count", 0),
        "task_count": dashboard.get("counts", {}).get("task_count", 0),
    }
```

## Test Fixtures

```python
@pytest.fixture
def mock_update_branch() -> MagicMock:
    branch = MagicMock()
    branch.key = 1
    branch.name = "stable-4.13"
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Stable 4.13 release branch",
            "created": "2026-01-15T00:00:00",
        }
        return data.get(key, default)
    branch.get = mock_get
    return branch

@pytest.fixture
def mock_update_package() -> MagicMock:
    pkg = MagicMock()
    pkg.key = "yb-core"
    pkg.name = "yb-core"
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "version": "4.13.1-12345",
            "type": "ybpkg",
            "optional": False,
            "description": "VergeOS Core Package",
            "branch": 1,
            "modified": "2026-02-08T00:00:00",
        }
        return data.get(key, default)
    pkg.get = mock_get
    return pkg

@pytest.fixture
def mock_update_source_package() -> MagicMock:
    pkg = MagicMock()
    pkg.key = 10
    pkg.name = "yb-core"
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "version": "4.13.2-12400",
            "downloaded": False,
            "optional": False,
            "description": "VergeOS Core Package",
            "branch": 1,
            "source": 1,
            "require_license_feature": "",
        }
        return data.get(key, default)
    pkg.get = mock_get
    return pkg

@pytest.fixture
def mock_update_log() -> MagicMock:
    log = MagicMock()
    log.key = 500
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "level": "audit",
            "text": "Update check completed",
            "timestamp": 1707000000000000,
            "user": "admin",
            "object_name": "system",
        }
        return data.get(key, default)
    log.get = mock_get
    return log

@pytest.fixture
def mock_update_dashboard() -> MagicMock:
    dashboard = MagicMock()
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "node_count": 3,
            "counts": {"event_count": 12, "task_count": 5},
            "logs": [],
            "packages": [],
            "branches": [],
            "settings": {},
        }
        return data.get(key, default)
    dashboard.get = mock_get
    return dashboard
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_branch_list` | Lists update branches |
| 2 | `test_branch_get_by_key` | Get branch by key |
| 3 | `test_branch_get_by_name` | Get branch by name |
| 4 | `test_package_list` | Lists installed packages |
| 5 | `test_package_list_by_branch` | `--branch stable-4.13` filter |
| 6 | `test_package_get` | Get package by name |
| 7 | `test_available_list` | Lists available packages |
| 8 | `test_available_list_by_source` | `--source test-source` filter |
| 9 | `test_available_list_downloaded` | `--downloaded` filter |
| 10 | `test_available_list_pending` | `--pending` filter |
| 11 | `test_available_get` | Get available package |
| 12 | `test_update_status_dashboard` | Shows dashboard summary |
| 13 | `test_update_log_list` | Lists update logs |
| 14 | `test_update_log_list_by_level` | `--level error` filter |
| 15 | `test_update_log_get` | Get single log entry |

## Task Checklist

- [x] Create `update_branch.py` with list + get commands
- [x] Create `update_package.py` with list + get commands
- [x] Create `update_available.py` with list + get commands (pending/downloaded filters)
- [x] Create `update_log.py` with list + get commands
- [x] Add `status` command (dashboard) to `update.py`
- [x] Register sub-commands in `update.py`: branch, package, available, log
- [x] Add mock fixtures to `conftest.py`
- [x] Create `test_update_branch.py`
- [x] Create `test_update_package.py`
- [x] Create `test_update_available.py`
- [x] Create `test_update_log.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
