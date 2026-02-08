# Phase 4e: NAS Volume Syncs Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg nas sync` commands for volume synchronization job management
**Depends on:** Phase 4b (NAS Volumes)
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add NAS volume sync management for data replication between volumes. Syncs can copy data between volumes on the same or different NAS services, supporting rsync and ysync (VergeSync) methods. The SDK exposes syncs via `client.volume_syncs` (NASVolumeSyncManager).

Volume syncs use **40-character hex string keys** and the `resolve_nas_resource()` utility from Phase 4b.

## Commands

```
vrg nas sync list [--service SERVICE] [--enabled | --disabled]
vrg nas sync get <SYNC>
vrg nas sync create --name NAME --service SERVICE --source-volume VOL --dest-volume VOL [--source-path PATH] [--dest-path PATH] [--description DESC] [--sync-method ysync|rsync] [--dest-delete MODE] [--workers N] [--include PATTERNS] [--exclude PATTERNS] [--preserve-acls | --no-preserve-acls] [--preserve-permissions | --no-preserve-permissions] [--preserve-owner | --no-preserve-owner] [--preserve-groups | --no-preserve-groups] [--preserve-mod-time | --no-preserve-mod-time] [--preserve-xattrs | --no-preserve-xattrs] [--copy-symlinks | --no-copy-symlinks] [--freeze-filesystem]
vrg nas sync update <SYNC> [--description DESC] [--source-path PATH] [--dest-path PATH] [--sync-method ysync|rsync] [--dest-delete MODE] [--workers N] [--include PATTERNS] [--exclude PATTERNS] [--preserve-acls | --no-preserve-acls] [--preserve-permissions | --no-preserve-permissions] [--preserve-owner | --no-preserve-owner] [--preserve-groups | --no-preserve-groups] [--preserve-mod-time | --no-preserve-mod-time] [--preserve-xattrs | --no-preserve-xattrs] [--copy-symlinks | --no-copy-symlinks] [--freeze-filesystem | --no-freeze-filesystem]
vrg nas sync delete <SYNC> [--yes]
vrg nas sync enable <SYNC>
vrg nas sync disable <SYNC>
vrg nas sync start <SYNC>
vrg nas sync stop <SYNC>
```

### Command Details

#### `list`
- Options:
  - `--service` (str, optional) — filter by NAS service name or key
  - `--enabled / --disabled` (optional)
- SDK: `client.volume_syncs.list(service=service, enabled=enabled)`

#### `get`
- Positional: `SYNC` (name or hex key)
- SDK: `client.volume_syncs.get(key=key)` or `get(name=name)`
- Uses `resolve_nas_resource()`

#### `create`
- Required: `--name`, `--service`, `--source-volume`, `--dest-volume`
- Options:
  - `--name / -n` (str, required)
  - `--service` (str, required) — NAS service name or key
  - `--source-volume` (str, required) — source volume name or key
  - `--dest-volume` (str, required) — destination volume name or key
  - `--source-path` (str, optional) — subdirectory within source volume
  - `--dest-path` (str, optional) — subdirectory within dest volume
  - `--description / -d` (str, optional)
  - `--sync-method` (str, default "ysync") — "ysync" or "rsync"
  - `--dest-delete` (str, default "never") — "never", "delete", "delete-before", "delete-during", "delete-delay", "delete-after"
  - `--workers` (int, default 4) — parallel workers (1-128)
  - `--include` (str, optional) — comma-separated include patterns
  - `--exclude` (str, optional) — comma-separated exclude patterns
  - `--preserve-acls / --no-preserve-acls` (bool, default True)
  - `--preserve-permissions / --no-preserve-permissions` (bool, default True)
  - `--preserve-owner / --no-preserve-owner` (bool, default True)
  - `--preserve-groups / --no-preserve-groups` (bool, default True)
  - `--preserve-mod-time / --no-preserve-mod-time` (bool, default True)
  - `--preserve-xattrs / --no-preserve-xattrs` (bool, default True)
  - `--copy-symlinks / --no-copy-symlinks` (bool, default True)
  - `--freeze-filesystem` (flag, default False) — freeze filesystem before snapshot
- SDK: `client.volume_syncs.create(name=..., service=..., source_volume=..., destination_volume=..., ...)`
- Include/exclude patterns: split comma-separated CLI input into Python lists for SDK (API stores as newline-delimited)

#### `update`
- Positional: `SYNC` (name or hex key)
- Same options as create minus --name, --service, --source-volume, --dest-volume
- SDK: `client.volume_syncs.update(key, ...)`

#### `delete`
- Positional: `SYNC`
- Options: `--yes / -y`
- SDK: `client.volume_syncs.delete(key)`

#### `enable` / `disable`
- SDK: `client.volume_syncs.enable(key)` / `disable(key)`

#### `start`
- Positional: `SYNC`
- Initiates synchronization
- SDK: `client.volume_syncs.start(key)`

#### `stop`
- Positional: `SYNC`
- Aborts running sync
- SDK: `client.volume_syncs.stop(key)`

## Files

### New Files

1. **`src/verge_cli/commands/nas_sync.py`**
   - Helpers: `_sync_to_dict()`, `_split_patterns()` (comma-split helper for include/exclude)
   - Commands: list, get, create, update, delete, enable, disable, start, stop

2. **`tests/unit/test_nas_sync.py`**
   - Fixture: `mock_nas_sync` — MagicMock with key="aabb...(40)", name="daily-backup", sync_method="ysync", status="idle", workers=4
   - Tests: see test plan

### Modified Files

3. **`src/verge_cli/commands/nas.py`**
   - Add: `from verge_cli.commands import nas_sync`
   - Add: `app.add_typer(nas_sync.app, name="sync")`

4. **`tests/conftest.py`**
   - Add fixture: `mock_nas_sync`

## Column Definitions

```python
NAS_SYNC_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("status", style_map={"idle": "dim", "syncing": "green", "error": "red"}),
    ColumnDef("sync_method", header="Method"),
    ColumnDef("workers"),
    ColumnDef("source_volume_key", header="Source Vol", wide_only=True),
    ColumnDef("destination_volume_key", header="Dest Vol", wide_only=True),
    ColumnDef("dest_delete", header="Dest Delete", wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

```python
def _sync_to_dict(sync: Any) -> dict[str, Any]:
    return {
        "$key": sync.key,
        "name": sync.name,
        "enabled": sync.get("enabled"),
        "status": sync.get("status"),
        "sync_method": sync.get("sync_method"),
        "workers": sync.get("workers"),
        "source_volume_key": sync.get("source_volume_key"),
        "destination_volume_key": sync.get("destination_volume_key"),
        "dest_delete": sync.get("destination_delete"),
        "description": sync.get("description", ""),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_sync_list` | Lists all sync jobs |
| 2 | `test_sync_list_by_service` | Filter by --service |
| 3 | `test_sync_get` | Get by name |
| 4 | `test_sync_get_by_hex_key` | Get by hex key |
| 5 | `test_sync_create` | Create with required args |
| 6 | `test_sync_create_with_options` | Create with --sync-method rsync, --workers, --include, --exclude |
| 7 | `test_sync_create_with_preserve_flags` | Create with --no-preserve-acls, --no-copy-symlinks |
| 8 | `test_sync_update` | Update workers and dest-delete |
| 9 | `test_sync_delete` | Delete with --yes |
| 10 | `test_sync_enable` | Enable sync |
| 11 | `test_sync_disable` | Disable sync |
| 12 | `test_sync_start` | Start sync |
| 13 | `test_sync_stop` | Stop running sync |
| 14 | `test_sync_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [ ] Create `src/verge_cli/commands/nas_sync.py` with all commands
- [ ] Register sub-typer in `nas.py`
- [ ] Add `mock_nas_sync` fixture to `conftest.py`
- [ ] Create `tests/unit/test_nas_sync.py` with all tests
- [ ] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [ ] Run `uv run pytest tests/unit/test_nas_sync.py -v`

## Notes

- Sync keys are 40-char hex strings
- Include/exclude patterns are comma-separated in CLI, converted to lists for SDK, stored as newline-delimited in API
- Sync method "ysync" = VergeSync (proprietary), "rsync" = standard rsync. SDK accepts friendly names like "vergesync" → "ysync"
- Destination delete modes: "never" (safe), "delete" (mirror), "delete-before/during/delay/after" (timing variants)
- Workers range: 1-128, default 4
- Start/stop use separate API endpoint (`volume_sync_actions`)
- Preservation flags default to True — most users want full fidelity copies
- Service resolution for `--service` uses existing `resolve_resource_id()` (int keys)
- Volume resolution for `--source-volume` and `--dest-volume` uses `resolve_nas_resource()` (hex keys)
