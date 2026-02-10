# Phase 8a: Catalog Repositories Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg catalog repo` commands — catalog repository CRUD, status, and logs
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Catalog Repositories | `catalog_repositories` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/catalogs.py` |
| Repository Logs | `catalog_repository_logs` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/catalogs.py` |
| Repository Status | `catalog_repository_status` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/catalogs.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/catalog_example.py`

---

## Overview

Add catalog repository management commands. Catalog repositories are the top-level containers in VergeOS's marketplace system — they point to a source of recipes/catalogs (local, remote, provider, etc.). This plan covers the repository CRUD operations plus the status and log sub-resources.

**Reference implementations:** `recipe.py` for CRUD pattern, `recipe_log.py` for log sub-command pattern.

## Commands

```
vrg catalog repo list [--filter ODATA] [--type TYPE] [--enabled | --disabled]
vrg catalog repo get <ID|NAME>
vrg catalog repo create --name NAME [--type local|remote|provider|remote-git|yottabyte] [--url URL] [--user USER] [--password PASSWORD] [--description DESC] [--allow-insecure] [--no-auto-refresh] [--max-tier TIER] [--override-default-scope none|private|global|tenant]
vrg catalog repo update <ID|NAME> [--name NAME] [--description DESC] [--url URL] [--user USER] [--password PASSWORD] [--allow-insecure BOOL] [--auto-refresh BOOL] [--max-tier TIER] [--override-default-scope SCOPE] [--enabled BOOL]
vrg catalog repo delete <ID|NAME> [--yes]
vrg catalog repo refresh <ID|NAME>
vrg catalog repo status <ID|NAME>
vrg catalog repo log list [--repo REPO] [--level LEVEL]
vrg catalog repo log get <KEY>
```

### Command Details

#### `vrg catalog repo list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--type` (str, choices: local/remote/provider/remote-git/yottabyte) — filter by repository type
  - `--enabled / --disabled` (flag pair) — filter by enabled state
- SDK: `catalog_repositories.list(type=type, enabled=enabled)`

#### `vrg catalog repo get`

- Positional: `REPO` (numeric key or name)
- Resolution: `resolve_resource_id(client.catalog_repositories, identifier, "Catalog repository")`
- SDK: `catalog_repositories.get(key)`

#### `vrg catalog repo create`

- Required: `--name`
- Optional: `--type` (default "local"), `--url`, `--user`, `--password`, `--description`, `--allow-insecure` (flag), `--no-auto-refresh` (flag, inverts `auto_refresh`), `--max-tier` (default "1"), `--override-default-scope` (default "none")
- SDK: `catalog_repositories.create(name=..., type=..., ...)`

#### `vrg catalog repo update`

- Positional: `REPO` (key or name)
- All fields optional — standard read-patch-write pattern
- SDK: `catalog_repositories.update(key, ...)`

#### `vrg catalog repo delete`

- Positional: `REPO` (key or name)
- `--yes / -y` — skip confirmation
- SDK: `catalog_repositories.delete(key)`

#### `vrg catalog repo refresh`

- Positional: `REPO` (key or name)
- Triggers a repository refresh to pull latest catalogs
- SDK: `catalog_repositories.refresh(key)`
- Output: success message

#### `vrg catalog repo status`

- Positional: `REPO` (key or name)
- Shows current repository sync/health status
- SDK: `catalog_repositories.get_status(key)` → returns `CatalogRepositoryStatus`
- Output: single-record table with status, state, info, last_update

#### `vrg catalog repo log list`

- Options:
  - `--repo` (str) — filter logs by repository name or key
  - `--level` (str) — filter by log level (message/warning/error/critical)
- SDK: `catalog_repository_logs.list(catalog_repository=repo_key, level=level)`

#### `vrg catalog repo log get`

- Positional: `KEY` (numeric log entry key)
- SDK: `catalog_repository_logs.get(key)`

## Files

### New Files

1. **`src/verge_cli/commands/catalog.py`** — Parent Typer app that registers `repo` sub-command
   - Just the `app = typer.Typer(...)` and `app.add_typer(catalog_repo.app, name="repo")`
   - Catalog-level commands (list, get, create, etc.) will be added in Phase 8b

2. **`src/verge_cli/commands/catalog_repo.py`** — Repository CRUD + refresh + status
   - Typer app: `repo`
   - Registers `catalog_repo_log.app` as sub-command `log`
   - Columns: `REPO_COLUMNS`, `REPO_STATUS_COLUMNS`
   - Helpers: `_repo_to_dict()`, `_status_to_dict()`

3. **`src/verge_cli/commands/catalog_repo_log.py`** — Repository log sub-commands
   - Pattern: mirrors `recipe_log.py`
   - Columns: `REPO_LOG_COLUMNS`
   - Helper: `_log_to_dict()`

4. **`tests/unit/test_catalog_repo.py`** — Tests for repo CRUD, refresh, status

5. **`tests/unit/test_catalog_repo_log.py`** — Tests for repo log commands

### Modified Files

6. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import catalog`
   - Add: `app.add_typer(catalog.app, name="catalog")`

7. **`tests/conftest.py`**
   - Add `mock_catalog_repo` fixture
   - Add `mock_catalog_repo_status` fixture
   - Add `mock_catalog_repo_log` fixture

## Column Definitions

### REPO_COLUMNS

```python
REPO_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("type"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Y": "green", "-": "red"}),
    ColumnDef("auto_refresh", header="Auto Refresh", format_fn=format_bool_yn),
    ColumnDef("url", wide_only=True),
    ColumnDef("description", wide_only=True),
    ColumnDef("max_tier", header="Max Tier", wide_only=True),
    ColumnDef("last_refreshed", header="Last Refreshed", wide_only=True),
]
```

### REPO_STATUS_COLUMNS

```python
REPO_STATUS_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("status", style_map={
        "online": "green", "refreshing": "yellow",
        "downloading": "cyan", "error": "red",
    }),
    ColumnDef("state"),
    ColumnDef("info"),
    ColumnDef("last_update", header="Last Update"),
]
```

### REPO_LOG_COLUMNS

```python
REPO_LOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level", style_map={"error": "red", "warning": "yellow", "critical": "red bold"}),
    ColumnDef("text", header="Message"),
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("user", wide_only=True),
]
```

## Data Mappings

```python
def _repo_to_dict(repo: Any) -> dict[str, Any]:
    return {
        "$key": int(repo.key),
        "name": repo.name,
        "type": repo.get("type", ""),
        "description": repo.get("description", ""),
        "url": repo.get("url", ""),
        "enabled": repo.get("enabled"),
        "auto_refresh": repo.get("auto_refresh"),
        "max_tier": repo.get("max_tier", ""),
        "last_refreshed": repo.get("last_refreshed", ""),
    }

def _status_to_dict(status: Any) -> dict[str, Any]:
    return {
        "$key": int(status.key),
        "status": status.get("status", ""),
        "state": status.get("state", ""),
        "info": status.get("info", ""),
        "last_update": status.get("last_update", ""),
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
        "user": log.get("user", ""),
    }
```

## Test Fixtures

```python
@pytest.fixture
def mock_catalog_repo() -> MagicMock:
    repo = MagicMock()
    repo.key = 1
    repo.name = "test-repo"
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "type": "local",
            "description": "Test repository",
            "url": "",
            "enabled": True,
            "auto_refresh": True,
            "max_tier": "1",
            "override_default_scope": "none",
            "last_refreshed": "2026-02-10T00:00:00",
        }
        return data.get(key, default)
    repo.get = mock_get
    return repo

@pytest.fixture
def mock_catalog_repo_status() -> MagicMock:
    status = MagicMock()
    status.key = 1
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "status": "online",
            "state": "online",
            "info": "",
            "last_update": "2026-02-10T00:00:00",
        }
        return data.get(key, default)
    status.get = mock_get
    return status

@pytest.fixture
def mock_catalog_repo_log() -> MagicMock:
    log = MagicMock()
    log.key = 100
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "catalog_repository": 1,
            "level": "message",
            "text": "Repository refreshed successfully",
            "timestamp": 1707000000000000,
            "user": "admin",
        }
        return data.get(key, default)
    log.get = mock_get
    return log
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_repo_list` | Lists repositories |
| 2 | `test_repo_list_by_type` | `--type remote` filter |
| 3 | `test_repo_list_enabled` | `--enabled` filter |
| 4 | `test_repo_get_by_key` | Get by numeric key |
| 5 | `test_repo_get_by_name` | Get by name (resolve) |
| 6 | `test_repo_create_local` | Create local repository |
| 7 | `test_repo_create_remote` | Create remote repo with URL/user/password |
| 8 | `test_repo_update` | Update description and URL |
| 9 | `test_repo_delete_confirm` | Delete with --yes |
| 10 | `test_repo_delete_no_confirm` | Delete without --yes aborts |
| 11 | `test_repo_refresh` | Trigger refresh |
| 12 | `test_repo_status` | Show repository status |
| 13 | `test_repo_log_list` | List repo logs |
| 14 | `test_repo_log_list_by_repo` | `--repo test-repo` filter |
| 15 | `test_repo_log_get` | Get single log entry |
| 16 | `test_repo_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [x] Create `catalog.py` parent app (minimal — just registers sub-commands)
- [x] Create `catalog_repo.py` with CRUD + refresh + status commands
- [x] Create `catalog_repo_log.py` with list + get commands
- [x] Register `catalog` in `cli.py`
- [x] Add mock fixtures to `conftest.py`
- [x] Create `test_catalog_repo.py`
- [x] Create `test_catalog_repo_log.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
