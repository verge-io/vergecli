# Phase 3e: Site Syncs Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg site sync` sub-commands for managing site synchronization (outgoing and incoming)
**Dependency:** Phase 3d (Sites) must be complete

---

## Overview

Add site sync management as nested sub-commands under `vrg site sync`. Site syncs are auto-created by the system and appear in the UI as sub-resources of sites. The SDK provides separate managers for outgoing syncs (`client.site_syncs`) and incoming syncs (`client.site_syncs_incoming`).

Unlike VMs or networks, syncs cannot be created or deleted via API — they are system-managed. Users can only enable/disable them and view their status.

## Commands

```
vrg site sync outgoing list [--site SITE] [--enabled/--disabled]
vrg site sync outgoing get <SYNC>
vrg site sync outgoing enable <SYNC>
vrg site sync outgoing disable <SYNC>

vrg site sync incoming list [--site SITE] [--enabled/--disabled]
vrg site sync incoming get <SYNC>
vrg site sync incoming enable <SYNC>
vrg site sync incoming disable <SYNC>
```

### Excluded Features

- No `add-to-queue` / manual trigger command (deferred)
- No sync schedules (deferred to later phase)

### Command Details

#### Outgoing Sync Commands

##### `list`
- Options:
  - `--site / -s` (str, optional) — Filter by site (name or key)
  - `--enabled` (flag) — Show only enabled syncs
  - `--disabled` (flag) — Show only disabled syncs
- `--enabled` and `--disabled` are mutually exclusive
- SDK: `client.site_syncs.list(site_name=..., enabled=...)` or `list_for_site(site_key)`

##### `get`
- Positional: `SYNC` (name or key)
- SDK: `client.site_syncs.get(key)` with name resolution

##### `enable`
- Positional: `SYNC` (name or key)
- SDK: `client.site_syncs.enable(key)`
- Output: Success message + sync details

##### `disable`
- Positional: `SYNC` (name or key)
- SDK: `client.site_syncs.disable(key)`
- Output: Success message + sync details

#### Incoming Sync Commands

##### `list`
- Options:
  - `--site / -s` (str, optional) — Filter by site (name or key)
  - `--enabled` (flag) — Show only enabled syncs
  - `--disabled` (flag) — Show only disabled syncs
- `--enabled` and `--disabled` are mutually exclusive
- SDK: `client.site_syncs_incoming.list(site_name=..., enabled=...)` or `list_for_site(site_key)`

##### `get`
- Positional: `SYNC` (name or key)
- SDK: `client.site_syncs_incoming.get(key)` with name resolution

##### `enable`
- Positional: `SYNC` (name or key)
- SDK: `client.site_syncs_incoming.enable(key)`
- Output: Success message + sync details

##### `disable`
- Positional: `SYNC` (name or key)
- SDK: `client.site_syncs_incoming.disable(key)`
- Output: Success message + sync details

## Files

### New Files

1. **`src/verge_cli/commands/site_sync.py`**
   - Parent Typer app for `sync` sub-command
   - Registers `outgoing` and `incoming` as nested sub-typers
   - Pattern: mirrors `network.py` which registers sub-typers

2. **`src/verge_cli/commands/site_sync_outgoing.py`**
   - Commands: list, get, enable, disable
   - Helper: `_resolve_sync()` — resolve sync name/key to int key
   - Helper: `_sync_to_dict()` — convert SDK object to output dict
   - SDK Manager: `client.site_syncs` (SiteSyncOutgoingManager)

3. **`src/verge_cli/commands/site_sync_incoming.py`**
   - Commands: list, get, enable, disable
   - Helper: `_resolve_sync()` — resolve sync name/key to int key
   - Helper: `_sync_to_dict()` — convert SDK object to output dict
   - SDK Manager: `client.site_syncs_incoming` (SiteSyncIncomingManager)

4. **`tests/unit/test_site_sync_outgoing.py`**
   - Fixture: `mock_sync_outgoing` — MagicMock with key=800, name="prod-to-backup"
   - Tests: see test plan below

5. **`tests/unit/test_site_sync_incoming.py`**
   - Fixture: `mock_sync_incoming` — MagicMock with key=900, name="backup-to-prod"
   - Tests: see test plan below

### Modified Files

6. **`src/verge_cli/commands/site.py`**
   - Add: `from verge_cli.commands import site_sync`
   - Add: `app.add_typer(site_sync.app, name="sync")`
   - **Note:** This file will be created in Phase 3d

7. **`src/verge_cli/columns.py`**
   - Add `SITE_SYNC_OUTGOING_COLUMNS` definition
   - Add `SITE_SYNC_INCOMING_COLUMNS` definition

## Column Definitions

### Outgoing Syncs

```python
SITE_SYNC_OUTGOING_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("site"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("state"),
    # wide-only
    ColumnDef("encryption", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("compression", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("threads", wide_only=True),
    ColumnDef("last_run", format_fn=format_epoch, wide_only=True),
    ColumnDef("destination_tier", header="Dest Tier", wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

### Incoming Syncs

```python
SITE_SYNC_INCOMING_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("site"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("state"),
    # wide-only
    ColumnDef("last_sync", format_fn=format_epoch, wide_only=True),
    ColumnDef("min_snapshots", header="Min Snapshots", wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

### Outgoing Sync

```python
def _sync_to_dict(sync: Any) -> dict[str, Any]:
    return {
        "$key": sync.key,
        "name": sync.name,
        "site": sync.get("site"),
        "status": sync.get("status"),
        "enabled": sync.get("enabled"),
        "state": sync.get("state"),
        "encryption": sync.get("encryption"),
        "compression": sync.get("compression"),
        "threads": sync.get("threads"),
        "last_run": sync.get("last_run"),
        "destination_tier": sync.get("destination_tier"),
        "description": sync.get("description", ""),
    }
```

### Incoming Sync

```python
def _sync_to_dict(sync: Any) -> dict[str, Any]:
    return {
        "$key": sync.key,
        "name": sync.name,
        "site": sync.get("site"),
        "status": sync.get("status"),
        "enabled": sync.get("enabled"),
        "state": sync.get("state"),
        "last_sync": sync.get("last_sync"),
        "min_snapshots": sync.get("min_snapshots"),
        "description": sync.get("description", ""),
    }
```

## Test Plan

### Outgoing Sync Tests

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_outgoing_list` | Lists all outgoing syncs |
| 2 | `test_outgoing_list_empty` | Handles empty list |
| 3 | `test_outgoing_list_by_site` | Filter by --site option |
| 4 | `test_outgoing_get` | Get by name resolution |
| 5 | `test_outgoing_get_by_key` | Get by numeric key |
| 6 | `test_outgoing_enable` | Enable sync by name |
| 7 | `test_outgoing_disable` | Disable sync by name |

### Incoming Sync Tests

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_incoming_list` | Lists all incoming syncs |
| 2 | `test_incoming_list_empty` | Handles empty list |
| 3 | `test_incoming_list_by_site` | Filter by --site option |
| 4 | `test_incoming_get` | Get by name resolution |
| 5 | `test_incoming_get_by_key` | Get by numeric key |
| 6 | `test_incoming_enable` | Enable sync by name |
| 7 | `test_incoming_disable` | Disable sync by name |

## Implementation Steps

**Prerequisites:** Phase 3d (Sites) must be complete with `site.py` available.

1. Add `SITE_SYNC_OUTGOING_COLUMNS` and `SITE_SYNC_INCOMING_COLUMNS` to `columns.py`
2. Create `site_sync_outgoing.py` with all commands
3. Create `site_sync_incoming.py` with all commands
4. Create `site_sync.py` (registers outgoing/incoming sub-typers)
5. Register `sync` sub-typer in `site.py`
6. Create `test_site_sync_outgoing.py` with all tests
7. Create `test_site_sync_incoming.py` with all tests
8. Run `uv run ruff check` and `uv run mypy src/verge_cli`
9. Run `uv run pytest tests/unit/test_site_sync_outgoing.py -v`
10. Run `uv run pytest tests/unit/test_site_sync_incoming.py -v`
11. Update PRD phase 3 checklist to mark Site Syncs done

## SDK Reference

### SiteSyncOutgoingManager

```python
client.site_syncs.list(
    filter: str | None = None,
    fields: list[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    site_key: int | None = None,
    site_name: str | None = None,
    enabled: bool | None = None,
) -> list[SiteSyncOutgoing]

client.site_syncs.list_enabled(fields: list[str] | None = None) -> list[SiteSyncOutgoing]
client.site_syncs.list_disabled(fields: list[str] | None = None) -> list[SiteSyncOutgoing]
client.site_syncs.list_for_site(
    site_key: int | None = None,
    site_name: str | None = None,
    fields: list[str] | None = None,
) -> list[SiteSyncOutgoing]

client.site_syncs.get(
    key: int | None = None,
    name: str | None = None,
    site_key: int | None = None,
    site_name: str | None = None,
    fields: list[str] | None = None,
) -> SiteSyncOutgoing

client.site_syncs.enable(key: int) -> SiteSyncOutgoing
client.site_syncs.disable(key: int) -> SiteSyncOutgoing
```

### SiteSyncIncomingManager

```python
client.site_syncs_incoming.list(
    filter: str | None = None,
    fields: list[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    site_key: int | None = None,
    site_name: str | None = None,
    enabled: bool | None = None,
) -> list[SiteSyncIncoming]

client.site_syncs_incoming.get(
    key: int | None = None,
    name: str | None = None,
    site_key: int | None = None,
    site_name: str | None = None,
    fields: list[str] | None = None,
) -> SiteSyncIncoming

client.site_syncs_incoming.enable(key: int) -> SiteSyncIncoming
client.site_syncs_incoming.disable(key: int) -> SiteSyncIncoming
```

## Notes

- Syncs are **system-managed** — no create/delete/update operations
- Enable/disable are the only state-change operations available
- Outgoing syncs push data to remote sites (backup/DR)
- Incoming syncs receive data from remote sites
- Both sync types are tied to site relationships
- Filter by site using either `site_key` or `site_name` (SDK supports both)
- Name resolution follows standard pattern: numeric = key, string = name lookup
