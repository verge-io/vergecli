# Phase 8c: Update Settings & Sources Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg update` commands — update settings, check/download/install operations, and update sources with status
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Update Settings | `update_settings` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |
| Update Sources | `update_sources` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |
| Source Status | `update_source_status` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/updates.py` |

**SDK example:** None (follow `system.py` singleton pattern for settings)

---

## Overview

Add system update management commands for VergeOS. This plan covers the core update workflow: viewing/configuring update settings, triggering check/download/install operations, and managing update sources.

**Key details:**
- `UpdateSettings` is a singleton (always key=1) — `get()` ignores the key parameter
- Update sources support CRUD plus a status sub-resource
- The `check` → `download` → `install` workflow is the standard update path
- `update_all()` is a convenience that does check + download + install in one step

**Reference implementations:** `system.py` for singleton-style commands, `recipe.py` for CRUD pattern.

## Commands

```
vrg update settings
vrg update configure [--source SOURCE] [--branch BRANCH] [--auto-refresh BOOL] [--auto-update BOOL] [--auto-reboot BOOL] [--update-time HH:MM] [--max-vsan-usage PCT] [--warm-reboot BOOL] [--multi-cluster-update BOOL] [--snapshot-on-update BOOL] [--snapshot-expire SECONDS] [--anonymize-stats BOOL]
vrg update check
vrg update download
vrg update install [--yes]
vrg update apply [--force] [--yes]
vrg update source list [--filter ODATA] [--enabled | --disabled]
vrg update source get <ID|NAME>
vrg update source create --name NAME --url URL [--description DESC] [--user USER] [--password PASSWORD] [--enabled | --no-enabled]
vrg update source update <ID|NAME> [--name NAME] [--description DESC] [--url URL] [--user USER] [--password PASSWORD] [--enabled BOOL]
vrg update source delete <ID|NAME> [--yes]
vrg update source status <ID|NAME>
```

### Command Details

#### `vrg update settings`

- No arguments — displays current update settings as a single-record table
- SDK: `update_settings.get()` → `UpdateSettings`
- Show key fields: source, branch, auto_refresh, auto_update, auto_reboot, update_time, installed, reboot_required, applying_updates

#### `vrg update configure`

- All options optional — only updates provided values
- Option mapping:
  - `--source` (int) — active update source key
  - `--branch` (int) — selected branch key
  - `--auto-refresh / --no-auto-refresh` (bool)
  - `--auto-update / --no-auto-update` (bool)
  - `--auto-reboot / --no-auto-reboot` (bool)
  - `--update-time` (str) — HH:MM format
  - `--max-vsan-usage` (int) — percentage
  - `--warm-reboot / --no-warm-reboot` (bool)
  - `--multi-cluster-update / --no-multi-cluster-update` (bool)
  - `--snapshot-on-update / --no-snapshot-on-update` (bool)
  - `--snapshot-expire` (int) — seconds
  - `--anonymize-stats / --no-anonymize-stats` (bool)
- SDK: `update_settings.update(source=..., branch=..., ...)`
- Output: updated settings + success message

#### `vrg update check`

- No arguments — checks for available updates
- SDK: `update_settings.check()`
- Output: result dict or success message

#### `vrg update download`

- No arguments — downloads available updates
- SDK: `update_settings.download()`
- Output: result dict or success message

#### `vrg update install`

- `--yes / -y` — skip confirmation (installing updates may require reboot)
- SDK: `update_settings.install()`
- Confirm before proceeding — updates may interrupt services
- Output: result dict or success message

#### `vrg update apply`

- `--force` (flag) — force update even if already up to date
- `--yes / -y` — skip confirmation
- Convenience: check + download + install in one step
- SDK: `update_settings.update_all(force=force)`
- Confirm before proceeding
- Output: result dict or success message

#### `vrg update source list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--enabled / --disabled` (flag pair)
- SDK: `update_sources.list(enabled=enabled)`

#### `vrg update source get`

- Positional: `SOURCE` (numeric key or name)
- Resolution: `resolve_resource_id(client.update_sources, identifier, "Update source")`
- SDK: `update_sources.get(key)`

#### `vrg update source create`

- Required: `--name`, `--url`
- Optional: `--description`, `--user`, `--password`, `--enabled / --no-enabled` (default enabled)
- SDK: `update_sources.create(name=..., url=..., ...)`

#### `vrg update source update`

- Positional: `SOURCE` (key or name)
- All fields optional
- SDK: `update_sources.update(key, ...)`

#### `vrg update source delete`

- Positional: `SOURCE` (key or name)
- `--yes / -y` — skip confirmation
- SDK: `update_sources.delete(key)`

#### `vrg update source status`

- Positional: `SOURCE` (key or name)
- Shows current update source sync status
- SDK: `update_sources.get_status(key)` → `UpdateSourceStatus`
- Output: single-record table with status, info, nodes_updated, last_update

## Files

### New Files

1. **`src/verge_cli/commands/update.py`** — Parent Typer app with settings, configure, check, download, install, apply commands
   - Registers `update_source.app` as sub-command `source`
   - Columns: `SETTINGS_COLUMNS`
   - Helpers: `_settings_to_dict()`

2. **`src/verge_cli/commands/update_source.py`** — Update source CRUD + status
   - Columns: `SOURCE_COLUMNS`, `SOURCE_STATUS_COLUMNS`
   - Helpers: `_source_to_dict()`, `_source_status_to_dict()`

3. **`tests/unit/test_update.py`** — Tests for settings, configure, check, download, install, apply

4. **`tests/unit/test_update_source.py`** — Tests for source CRUD + status

### Modified Files

5. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import update`
   - Add: `app.add_typer(update.app, name="update")`

6. **`tests/conftest.py`**
   - Add `mock_update_settings` fixture
   - Add `mock_update_source` fixture
   - Add `mock_update_source_status` fixture

## Column Definitions

### SETTINGS_COLUMNS

```python
SETTINGS_COLUMNS: list[ColumnDef] = [
    ColumnDef("source", header="Source"),
    ColumnDef("branch", header="Branch"),
    ColumnDef("auto_refresh", header="Auto Refresh", format_fn=format_bool_yn),
    ColumnDef("auto_update", header="Auto Update", format_fn=format_bool_yn),
    ColumnDef("auto_reboot", header="Auto Reboot", format_fn=format_bool_yn),
    ColumnDef("update_time", header="Update Time"),
    ColumnDef("installed", header="Installed", format_fn=format_bool_yn, style_map={"Y": "green", "-": "dim"}),
    ColumnDef("reboot_required", header="Reboot Req", format_fn=format_bool_yn, style_map={"Y": "yellow", "-": "dim"}),
    ColumnDef("applying_updates", header="Applying", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("warm_reboot", header="Warm Reboot", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("multi_cluster_update", header="Multi-Cluster", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("snapshot_on_update", header="Snapshot", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("max_vsan_usage", header="Max vSAN%", wide_only=True),
]
```

### SOURCE_COLUMNS

```python
SOURCE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("url"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Y": "green", "-": "red"}),
    ColumnDef("description", wide_only=True),
    ColumnDef("last_refreshed", header="Last Refreshed", wide_only=True),
    ColumnDef("last_updated", header="Last Updated", wide_only=True),
]
```

### SOURCE_STATUS_COLUMNS

```python
SOURCE_STATUS_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("status", style_map={
        "idle": "green", "refreshing": "yellow",
        "downloading": "cyan", "installing": "yellow",
        "applying": "yellow", "error": "red",
    }),
    ColumnDef("info"),
    ColumnDef("nodes_updated", header="Nodes Updated"),
    ColumnDef("last_update", header="Last Update"),
]
```

## Data Mappings

```python
def _settings_to_dict(settings: Any) -> dict[str, Any]:
    return {
        "source": settings.get("source", ""),
        "branch": settings.get("branch", ""),
        "auto_refresh": settings.get("auto_refresh"),
        "auto_update": settings.get("auto_update"),
        "auto_reboot": settings.get("auto_reboot"),
        "update_time": settings.get("update_time", ""),
        "max_vsan_usage": settings.get("max_vsan_usage", ""),
        "warm_reboot": settings.get("warm_reboot"),
        "multi_cluster_update": settings.get("multi_cluster_update"),
        "snapshot_on_update": settings.get("snapshot_cloud_on_update"),
        "installed": settings.get("installed"),
        "reboot_required": settings.get("reboot_required"),
        "applying_updates": settings.get("applying_updates"),
    }

def _source_to_dict(source: Any) -> dict[str, Any]:
    return {
        "$key": int(source.key),
        "name": source.name,
        "description": source.get("description", ""),
        "url": source.get("url", ""),
        "enabled": source.get("enabled"),
        "last_updated": source.get("last_updated", ""),
        "last_refreshed": source.get("last_refreshed", ""),
    }

def _source_status_to_dict(status: Any) -> dict[str, Any]:
    return {
        "$key": int(status.key),
        "status": status.get("status", ""),
        "info": status.get("info", ""),
        "nodes_updated": status.get("nodes_updated", ""),
        "last_update": status.get("last_update", ""),
    }
```

## Test Fixtures

```python
@pytest.fixture
def mock_update_settings() -> MagicMock:
    settings = MagicMock()
    settings.key = 1
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "source": 1,
            "branch": 1,
            "auto_refresh": True,
            "auto_update": False,
            "auto_reboot": False,
            "update_time": "02:00",
            "max_vsan_usage": 80,
            "warm_reboot": True,
            "multi_cluster_update": False,
            "snapshot_cloud_on_update": True,
            "snapshot_cloud_expire_seconds": 86400,
            "installed": False,
            "reboot_required": False,
            "applying_updates": False,
            "anonymize_statistics": False,
        }
        return data.get(key, default)
    settings.get = mock_get
    return settings

@pytest.fixture
def mock_update_source() -> MagicMock:
    source = MagicMock()
    source.key = 1
    source.name = "test-source"
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Default update source",
            "url": "https://updates.verge.io",
            "enabled": True,
            "last_updated": "2026-02-10T00:00:00",
            "last_refreshed": "2026-02-10T00:00:00",
        }
        return data.get(key, default)
    source.get = mock_get
    return source

@pytest.fixture
def mock_update_source_status() -> MagicMock:
    status = MagicMock()
    status.key = 1
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "source": 1,
            "status": "idle",
            "info": "",
            "nodes_updated": 2,
            "last_update": "2026-02-10T00:00:00",
        }
        return data.get(key, default)
    status.get = mock_get
    return status
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_update_settings` | Show current settings |
| 2 | `test_update_configure` | Update auto_refresh + update_time |
| 3 | `test_update_configure_booleans` | Toggle auto_update, auto_reboot |
| 4 | `test_update_check` | Check for updates |
| 5 | `test_update_download` | Download updates |
| 6 | `test_update_install_confirm` | Install with --yes |
| 7 | `test_update_install_no_confirm` | Install without --yes aborts |
| 8 | `test_update_apply_confirm` | Apply with --yes |
| 9 | `test_update_apply_force` | Apply with --force --yes |
| 10 | `test_source_list` | Lists update sources |
| 11 | `test_source_list_enabled` | `--enabled` filter |
| 12 | `test_source_get_by_key` | Get by numeric key |
| 13 | `test_source_get_by_name` | Get by name (resolve) |
| 14 | `test_source_create` | Create source with name + url |
| 15 | `test_source_create_with_auth` | Create source with user + password |
| 16 | `test_source_update` | Update URL |
| 17 | `test_source_delete_confirm` | Delete with --yes |
| 18 | `test_source_delete_no_confirm` | Delete without --yes aborts |
| 19 | `test_source_status` | Show source status |
| 20 | `test_source_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [x] Create `update.py` with settings, configure, check, download, install, apply commands
- [x] Create `update_source.py` with CRUD + status commands
- [x] Register `update_source` as sub-command of `update`
- [x] Register `update` in `cli.py`
- [x] Add mock fixtures to `conftest.py`
- [x] Create `test_update.py`
- [x] Create `test_update_source.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
