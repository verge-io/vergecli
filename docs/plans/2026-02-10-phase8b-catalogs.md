# Phase 8b: Catalogs & Catalog Logs Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg catalog` top-level commands — catalog CRUD, enable/disable, and catalog logs
**Dependencies:** Phase 8a (`catalog.py` parent app must exist)
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Catalogs | `catalogs` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/catalogs.py` |
| Catalog Logs | `catalog_logs` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/catalogs.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/catalog_example.py`

---

## Overview

Add catalog management commands to the `vrg catalog` app created in Phase 8a. Catalogs live inside catalog repositories and represent individual collections of VM recipes. Each catalog has a 40-character hex string key (not integer), similar to NAS resources. This plan also adds the catalog log sub-command.

**Key detail:** Catalog keys are 40-char hex strings — use `resolve_nas_resource()` from `utils.py` (not `resolve_resource_id()` which returns `int`).

**Reference implementations:** `recipe.py` for hex-key CRUD, `recipe_log.py` for log sub-command.

## Commands

```
vrg catalog list [--filter ODATA] [--repo REPO] [--enabled | --disabled]
vrg catalog get <ID|NAME>
vrg catalog create --name NAME --repo REPO [--description DESC] [--publishing-scope private|global|tenant] [--enabled | --no-enabled]
vrg catalog update <ID|NAME> [--name NAME] [--description DESC] [--publishing-scope SCOPE] [--enabled BOOL]
vrg catalog delete <ID|NAME> [--yes]
vrg catalog enable <ID|NAME>
vrg catalog disable <ID|NAME>
vrg catalog log list [--catalog CATALOG] [--level LEVEL]
vrg catalog log get <KEY>
```

### Command Details

#### `vrg catalog list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--repo` (str) — filter by repository name or key (resolve repo first)
  - `--enabled / --disabled` (flag pair) — filter by enabled state
- SDK: `catalogs.list(repository=repo_key, enabled=enabled)`

#### `vrg catalog get`

- Positional: `CATALOG` (40-char hex key or name)
- Resolution: `resolve_nas_resource(client.catalogs, identifier, resource_type="catalog")`
- SDK: `catalogs.get(key)`

#### `vrg catalog create`

- Required: `--name`, `--repo` (repository name or key)
- Optional: `--description`, `--publishing-scope` (default "private"), `--enabled / --no-enabled` (default enabled)
- Resolve `--repo` to repository key: `resolve_resource_id(client.catalog_repositories, repo, "Catalog repository")`
- SDK: `catalogs.create(name=..., repository=repo_key, ...)`

#### `vrg catalog update`

- Positional: `CATALOG` (hex key or name)
- All fields optional
- SDK: `catalogs.update(key, ...)`

#### `vrg catalog delete`

- Positional: `CATALOG` (hex key or name)
- `--yes / -y` — skip confirmation
- SDK: `catalogs.delete(key)`

#### `vrg catalog enable`

- Positional: `CATALOG` (hex key or name)
- Convenience command — equivalent to `vrg catalog update <id> --enabled`
- SDK: `catalogs.update(key, enabled=True)`
- Output: success message

#### `vrg catalog disable`

- Positional: `CATALOG` (hex key or name)
- Convenience command — equivalent to `vrg catalog update <id> --no-enabled`
- SDK: `catalogs.update(key, enabled=False)`
- Output: success message

#### `vrg catalog log list`

- Options:
  - `--catalog` (str) — filter by catalog name or hex key
  - `--level` (str) — filter by log level
- Resolve catalog: `resolve_nas_resource(client.catalogs, catalog, resource_type="catalog")`
- SDK: `catalog_logs.list(catalog=catalog_key, level=level)`

#### `vrg catalog log get`

- Positional: `KEY` (numeric log entry key)
- SDK: `catalog_logs.get(key)`

## Files

### New Files

1. **`src/verge_cli/commands/catalog_log.py`** — Catalog log sub-commands
   - Pattern: mirrors `recipe_log.py`
   - Columns: `CATALOG_LOG_COLUMNS`
   - Helper: `_log_to_dict()`

2. **`tests/unit/test_catalog.py`** — Tests for catalog CRUD, enable/disable

3. **`tests/unit/test_catalog_log.py`** — Tests for catalog log commands

### Modified Files

4. **`src/verge_cli/commands/catalog.py`** (created in 8a)
   - Add catalog-level commands: list, get, create, update, delete, enable, disable
   - Register `catalog_log.app` as sub-command `log`
   - Add: `CATALOG_COLUMNS`
   - Add: `_catalog_to_dict()`
   - Add: `_resolve_catalog()` helper using `resolve_nas_resource()`

5. **`tests/conftest.py`**
   - Add `mock_catalog` fixture (hex key)
   - Add `mock_catalog_log` fixture

## Column Definitions

### CATALOG_COLUMNS

```python
CATALOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("repository", header="Repository"),
    ColumnDef("publishing_scope", header="Scope"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Y": "green", "-": "red"}),
    ColumnDef("description", wide_only=True),
    ColumnDef("created", wide_only=True),
]
```

### CATALOG_LOG_COLUMNS

```python
CATALOG_LOG_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("level", style_map={"error": "red", "warning": "yellow", "critical": "red bold"}),
    ColumnDef("text", header="Message"),
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("user", wide_only=True),
]
```

## Data Mappings

```python
def _catalog_to_dict(catalog: Any) -> dict[str, Any]:
    return {
        "$key": catalog.key,  # hex string, not int
        "name": catalog.name,
        "repository": catalog.get("repository", ""),
        "description": catalog.get("description", ""),
        "publishing_scope": catalog.get("publishing_scope", ""),
        "enabled": catalog.get("enabled"),
        "created": catalog.get("created", ""),
    }

def _resolve_catalog(vctx: Any, identifier: str) -> str:
    """Resolve catalog identifier to hex key."""
    return resolve_nas_resource(
        vctx.client.catalogs,
        identifier,
        resource_type="catalog",
    )
```

## Test Fixtures

```python
@pytest.fixture
def mock_catalog() -> MagicMock:
    catalog = MagicMock()
    catalog.key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    catalog.name = "test-catalog"
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "repository": 1,
            "description": "Test catalog",
            "publishing_scope": "private",
            "enabled": True,
            "created": "2026-02-10T00:00:00",
        }
        return data.get(key, default)
    catalog.get = mock_get
    return catalog

@pytest.fixture
def mock_catalog_log() -> MagicMock:
    log = MagicMock()
    log.key = 200
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "catalog": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            "level": "message",
            "text": "Catalog synced successfully",
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
| 1 | `test_catalog_list` | Lists catalogs |
| 2 | `test_catalog_list_by_repo` | `--repo test-repo` filter (resolves repo key) |
| 3 | `test_catalog_list_enabled` | `--enabled` filter |
| 4 | `test_catalog_get_by_key` | Get by hex key |
| 5 | `test_catalog_get_by_name` | Get by name (resolve) |
| 6 | `test_catalog_create` | Create with name + repo |
| 7 | `test_catalog_create_with_scope` | Create with publishing scope |
| 8 | `test_catalog_update` | Update description |
| 9 | `test_catalog_delete_confirm` | Delete with --yes |
| 10 | `test_catalog_delete_no_confirm` | Delete without --yes aborts |
| 11 | `test_catalog_enable` | Enable a catalog |
| 12 | `test_catalog_disable` | Disable a catalog |
| 13 | `test_catalog_log_list` | List catalog logs |
| 14 | `test_catalog_log_list_by_catalog` | `--catalog test-catalog` filter |
| 15 | `test_catalog_log_get` | Get single log entry |
| 16 | `test_catalog_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [x] Add catalog-level commands to `catalog.py` (list, get, create, update, delete, enable, disable)
- [x] Create `catalog_log.py` with list + get commands
- [x] Register `catalog_log` in `catalog.py`
- [x] Add `mock_catalog` and `mock_catalog_log` fixtures to `conftest.py`
- [x] Create `test_catalog.py`
- [x] Create `test_catalog_log.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
