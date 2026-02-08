# Phase 3d: Sites Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg site` commands for multi-site management
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add site management as a top-level command group `vrg site`, enabling management of remote VergeOS sites for replication, cloud snapshots, and multi-site operations. Sites are VergeOS systems registered for inter-site communication. The SDK exposes sites via `client.sites` (SiteManager).

Phase 3e (site syncs) will add sub-typers for `vrg site sync incoming` and `vrg site sync outgoing` commands.

## Commands

```
vrg site list [--status STATUS] [--enabled/--disabled]
vrg site get <SITE>
vrg site create --name NAME --url URL --username USER --password PASS [options]
vrg site update <SITE> [--name NAME] [--description DESC] [--cloud-snapshots disabled|send|receive|both]
vrg site delete <SITE> [--yes]
vrg site enable <SITE>
vrg site disable <SITE>
vrg site reauth <SITE> --username USER --password PASS
vrg site refresh <SITE>
```

### Command Details

#### `list`
- Options:
  - `--status / -s` (str) — filter by status (e.g., "online", "offline")
  - `--enabled / --disabled` (flags) — filter by enabled state
- Lists all registered sites
- SDK: `client.sites.list(status=..., enabled=...)`

#### `get`
- Positional: `SITE` (name or key)
- Shows detailed site information
- SDK: `client.sites.get(key)`

#### `create`
- Required options:
  - `--name / -n` (str) — site name
  - `--url` (str) — site URL (e.g., "https://site2.example.com")
  - `--username` (str) — authentication username
  - `--password` (str) — authentication password
- Optional options:
  - `--description / -d` (str, default "") — description
  - `--allow-insecure` (flag) — allow insecure SSL connections
  - `--cloud-snapshots` (choice: disabled|send|receive|both, default "disabled")
  - `--auto-create-syncs / --no-auto-create-syncs` (bool, default True)
- Auth is options-only (no interactive prompts) to keep it scriptable
- SDK: `client.sites.create(name=..., url=..., username=..., password=..., ...)`

#### `update`
- Positional: `SITE` (name or key)
- Options:
  - `--name / -n` (str, optional) — new site name
  - `--description / -d` (str, optional) — description
  - `--cloud-snapshots` (choice: disabled|send|receive|both, optional)
- SDK: `client.sites.update(key, name=..., description=..., config_cloud_snapshots=...)`

#### `delete`
- Positional: `SITE` (name or key)
- Options: `--yes / -y` — skip confirmation
- SDK: `client.sites.delete(key)`

#### `enable`
- Positional: `SITE` (name or key)
- Enable a disabled site
- SDK: `client.sites.enable(key)`

#### `disable`
- Positional: `SITE` (name or key)
- Disable a site without deleting it
- SDK: `client.sites.disable(key)`

#### `reauth`
- Positional: `SITE` (name or key)
- Required options:
  - `--username` (str) — new username
  - `--password` (str) — new password
- Re-authenticate with updated credentials
- SDK: `client.sites.reauthenticate(key, username, password)`

#### `refresh`
- Positional: `SITE` (name or key)
- Refresh site connection and metadata
- SDK: `client.sites.refresh_site(key)`

## Files

### New Files

1. **`src/verge_cli/commands/site.py`**
   - Helper: `_site_to_dict()` — convert SDK object to output dict
   - Commands: list, get, create, update, delete, enable, disable, reauth, refresh
   - Pattern: top-level resource like `network.py`

2. **`tests/unit/test_site.py`**
   - Fixture: `mock_site` — MagicMock with key=800, name="site2"
   - Tests: see test plan below

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import site`
   - Add: `app.add_typer(site.app, name="site")`

4. **`src/verge_cli/columns.py`**
   - Add `SITE_COLUMNS` definition

## Column Definition

```python
SITE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("url", header="URL"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("authentication_status", header="Auth Status"),
    # wide-only
    ColumnDef("config_cloud_snapshots", header="Cloud Snapshots", wide_only=True),
    ColumnDef("description", wide_only=True),
    ColumnDef("domain", wide_only=True),
    ColumnDef("city", wide_only=True),
    ColumnDef("country", wide_only=True),
]
```

## Data Mapping

```python
def _site_to_dict(site: Any) -> dict[str, Any]:
    return {
        "$key": site.key,
        "name": site.name,
        "url": site.get("url"),
        "status": site.get("status"),
        "enabled": site.get("enabled"),
        "authentication_status": site.get("authentication_status"),
        "config_cloud_snapshots": site.get("config_cloud_snapshots"),
        "description": site.get("description", ""),
        "domain": site.get("domain"),
        "city": site.get("city"),
        "country": site.get("country"),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_site_list` | Lists all sites |
| 2 | `test_site_list_empty` | Handles empty list |
| 3 | `test_site_list_by_status` | --status filter |
| 4 | `test_site_list_enabled` | --enabled flag |
| 5 | `test_site_get` | Get by name resolution |
| 6 | `test_site_get_by_key` | Get by numeric key |
| 7 | `test_site_create` | Basic create with required options |
| 8 | `test_site_create_with_options` | --allow-insecure, --cloud-snapshots, --auto-create-syncs |
| 9 | `test_site_update` | Update name, description, cloud-snapshots |
| 10 | `test_site_delete` | Delete with --yes |
| 11 | `test_site_enable` | Enable disabled site |
| 12 | `test_site_disable` | Disable site |
| 13 | `test_site_reauth` | Re-authenticate with new credentials |
| 14 | `test_site_refresh` | Refresh site connection |

## Task Checklist

- [x] Add `SITE_COLUMNS` to `columns.py`
- [x] Create `site.py` with all commands
- [x] Register top-level typer in `cli.py`
- [x] Create `test_site.py` with all tests
- [x] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [x] Run `uv run pytest tests/unit/test_site.py -v`

## SDK Reference

**Manager:** `client.sites` (SiteManager)

**Key Methods:**
- `list(filter, fields, limit, offset, enabled=None, status=None)` → list[Site]
- `get(key=None, name=None, fields=None)` → Site
- `create(name, url, username, password, description=None, allow_insecure=False, config_cloud_snapshots="disabled", auto_create_syncs=True, ...)` → Site
- `update(key, name=None, description=None, enabled=None, config_cloud_snapshots=None, ...)` → Site
- `delete(key)` → None
- `enable(key)` → Site
- `disable(key)` → Site
- `reauthenticate(key, username, password)` → Site
- `refresh_site(key)` → Site

**Key Fields:**
- `$key`, `name`, `description`, `enabled`, `url`
- `status`, `status_info`, `authentication_status`
- `config_cloud_snapshots`, `config_statistics`, `config_management`, `config_repair_server`
- `domain`, `city`, `country`, `timezone`
- `is_tenant`, `incoming_syncs_enabled`, `outgoing_syncs_enabled`

## Notes

- Auth credentials (--username, --password) are required options only, no interactive prompts
- Site syncs (Phase 3e) will register as sub-typers later: `vrg site sync incoming|outgoing ...`
- Cloud snapshots config values: "disabled", "send", "receive", "both"
- Sites can be enabled/disabled without deletion for temporary disconnection
